from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .exceptions import (
    AccountInactive,
    OtpConsumed,
    OtpExpired,
    OtpInvalid,
    OtpRateLimited,
)
from .models import OtpChallenge, OtpRequestState, PlayerProfile, User
from .otp import (
    OtpDelivery,
    OtpDeliveryUnavailable,
    generate_otp_code,
    get_otp_sender,
)
from .phone import normalize_iran_mobile


@dataclass(frozen=True, slots=True)
class IssuedOtp:
    challenge: OtpChallenge
    expires_in: int
    resend_after: int


def _seconds_until(moment, now) -> int:
    return max(1, int((moment - now).total_seconds()))


def _rewind_failed_delivery(*, challenge: OtpChallenge, issued_at) -> None:
    failure_time = timezone.now()
    with transaction.atomic():
        locked_challenge = OtpChallenge.objects.select_for_update().get(pk=challenge.pk)
        if locked_challenge.consumed_at is None:
            locked_challenge.consumed_at = failure_time
            locked_challenge.save(update_fields=["consumed_at"])

        state = OtpRequestState.objects.select_for_update().get(phone=challenge.phone)
        if state.last_sent_at == issued_at:
            state.last_sent_at = None
            state.request_count = max(0, state.request_count - 1)
            if state.request_count == 0:
                state.window_started_at = None
            state.save(
                update_fields=[
                    "last_sent_at",
                    "request_count",
                    "window_started_at",
                    "updated_at",
                ]
            )


def issue_login_otp(*, phone: str, request_ip: str | None = None) -> IssuedOtp:
    phone = normalize_iran_mobile(phone)
    now = timezone.now()
    cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
    window_seconds = settings.OTP_REQUEST_WINDOW_SECONDS
    max_requests = settings.OTP_MAX_REQUESTS_PER_WINDOW
    ttl = settings.OTP_CODE_TTL_SECONDS

    with transaction.atomic():
        state, _ = OtpRequestState.objects.select_for_update().get_or_create(phone=phone)

        if state.last_sent_at:
            resend_at = state.last_sent_at + timedelta(seconds=cooldown)
            if now < resend_at:
                raise OtpRateLimited(
                    "برای درخواست کد جدید کمی صبر کنید.",
                    retry_after=_seconds_until(resend_at, now),
                )

        window_expired = (
            not state.window_started_at
            or now >= state.window_started_at + timedelta(seconds=window_seconds)
        )
        if window_expired:
            state.window_started_at = now
            state.request_count = 0

        if state.request_count >= max_requests:
            retry_at = state.window_started_at + timedelta(seconds=window_seconds)
            raise OtpRateLimited(
                "تعداد درخواست‌های کد موقتاً بیش از حد مجاز است.",
                retry_after=_seconds_until(retry_at, now),
            )

        state.request_count += 1
        state.last_sent_at = now
        state.save(
            update_fields=["window_started_at", "request_count", "last_sent_at", "updated_at"]
        )

        OtpChallenge.objects.filter(
            phone=phone,
            purpose=OtpChallenge.Purpose.LOGIN,
            consumed_at__isnull=True,
        ).update(consumed_at=now)

        code = generate_otp_code()
        challenge = OtpChallenge.objects.create(
            phone=phone,
            purpose=OtpChallenge.Purpose.LOGIN,
            code_hash=make_password(code),
            attempts_remaining=settings.OTP_MAX_VERIFY_ATTEMPTS,
            request_ip=request_ip,
            expires_at=now + timedelta(seconds=ttl),
        )

    try:
        get_otp_sender().send(OtpDelivery(phone=phone, code=code))
    except OtpDeliveryUnavailable:
        _rewind_failed_delivery(challenge=challenge, issued_at=now)
        raise

    return IssuedOtp(challenge=challenge, expires_in=ttl, resend_after=cooldown)


def verify_login_otp(*, challenge_id: UUID, code: str) -> User:
    now = timezone.now()
    pending_error = None
    user = None

    with transaction.atomic():
        try:
            challenge = OtpChallenge.objects.select_for_update().get(
                id=challenge_id,
                purpose=OtpChallenge.Purpose.LOGIN,
            )
        except OtpChallenge.DoesNotExist as exc:
            raise OtpInvalid("کد یا درخواست ورود معتبر نیست.") from exc

        if challenge.consumed_at is not None:
            pending_error = OtpConsumed("این کد قبلاً استفاده شده است.")
        elif now >= challenge.expires_at:
            challenge.consumed_at = now
            challenge.save(update_fields=["consumed_at"])
            pending_error = OtpExpired("کد ورود منقضی شده است.")
        elif challenge.attempts_remaining <= 0:
            challenge.consumed_at = now
            challenge.save(update_fields=["consumed_at"])
            pending_error = OtpInvalid("تعداد تلاش‌های مجاز به پایان رسیده است.")
        elif not check_password(code, challenge.code_hash):
            challenge.attempts_remaining -= 1
            update_fields = ["attempts_remaining"]
            if challenge.attempts_remaining <= 0:
                challenge.consumed_at = now
                update_fields.append("consumed_at")
            challenge.save(update_fields=update_fields)
            pending_error = OtpInvalid("کد ورود صحیح نیست.")
        else:
            challenge.consumed_at = now
            challenge.save(update_fields=["consumed_at"])
            user = User.objects.filter(phone=challenge.phone).first()
            if user is None:
                user = User.objects.create_user(phone=challenge.phone)
            PlayerProfile.objects.get_or_create(user=user)

    if pending_error is not None:
        raise pending_error
    if user is None:
        raise OtpInvalid("ورود تکمیل نشد.")
    if not user.is_active:
        raise AccountInactive("این حساب غیرفعال است.")

    return user
