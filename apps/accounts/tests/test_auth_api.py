from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import OtpChallenge, OtpRequestState, PlayerProfile, User
from apps.accounts.otp import MemoryOtpSender

OTP_REQUEST_URL = "/api/v1/auth/otp/request/"
OTP_VERIFY_URL = "/api/v1/auth/otp/verify/"
ME_URL = "/api/v1/auth/me/"
PROFILE_URL = "/api/v1/auth/me/profile/"
LOGOUT_URL = "/api/v1/auth/logout/"
CSRF_URL = "/api/v1/auth/csrf/"


@pytest.fixture(autouse=True)
def clear_otp_outbox():
    MemoryOtpSender.clear()
    yield
    MemoryOtpSender.clear()


def request_otp(client: APIClient, phone: str = "09121234567"):
    response = client.post(OTP_REQUEST_URL, {"phone": phone}, format="json")
    assert response.status_code == 201
    assert MemoryOtpSender.outbox
    return response, MemoryOtpSender.outbox[-1]


@pytest.mark.django_db
def test_otp_login_creates_account_profile_session_and_private_me_contract():
    client = APIClient()
    issued, delivery = request_otp(client, "۰۹۱۲۱۲۳۴۵۶۷")

    response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": delivery.code},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["phone"] == "+989121234567"
    user = User.objects.get(phone="+989121234567")
    assert user.has_usable_password() is False
    assert PlayerProfile.objects.filter(user=user).exists()

    me = client.get(ME_URL)
    assert me.status_code == 200
    assert me.data["id"] == str(user.id)
    assert me.data["profile"]["gamer_tag"] is None


@pytest.mark.django_db
def test_wrong_otp_persists_attempt_decrement_without_creating_user():
    client = APIClient()
    issued, delivery = request_otp(client)
    wrong_code = "000000" if delivery.code != "000000" else "111111"

    response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": wrong_code},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "otp_invalid"
    challenge = OtpChallenge.objects.get(id=issued.data["challenge_id"])
    assert challenge.attempts_remaining == 4
    assert challenge.consumed_at is None
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_expired_otp_is_consumed_and_cannot_be_replayed():
    client = APIClient()
    issued, delivery = request_otp(client)
    challenge = OtpChallenge.objects.get(id=issued.data["challenge_id"])
    challenge.expires_at = timezone.now() - timedelta(seconds=1)
    challenge.save(update_fields=["expires_at"])

    response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": delivery.code},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "otp_expired"
    challenge.refresh_from_db()
    assert challenge.consumed_at is not None

    replay = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": delivery.code},
        format="json",
    )
    assert replay.status_code == 400
    assert replay.data["error"]["code"] == "otp_consumed"


@pytest.mark.django_db
def test_successful_otp_is_single_use():
    client = APIClient()
    issued, delivery = request_otp(client)
    payload = {"challenge_id": issued.data["challenge_id"], "code": delivery.code}

    assert client.post(OTP_VERIFY_URL, payload, format="json").status_code == 200
    replay = client.post(OTP_VERIFY_URL, payload, format="json")
    assert replay.status_code == 400
    assert replay.data["error"]["code"] == "otp_consumed"


@pytest.mark.django_db
@override_settings(OTP_RESEND_COOLDOWN_SECONDS=0)
def test_new_otp_invalidates_previous_challenge():
    client = APIClient()
    first, first_delivery = request_otp(client)
    second, second_delivery = request_otp(client)

    old_response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": first.data["challenge_id"], "code": first_delivery.code},
        format="json",
    )
    assert old_response.status_code == 400
    assert old_response.data["error"]["code"] == "otp_consumed"

    current_response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": second.data["challenge_id"], "code": second_delivery.code},
        format="json",
    )
    assert current_response.status_code == 200


@pytest.mark.django_db
def test_resend_cooldown_returns_retry_after():
    client = APIClient()
    request_otp(client)

    response = client.post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json")

    assert response.status_code == 429
    assert response.data["error"]["code"] == "otp_rate_limited"
    assert int(response["Retry-After"]) >= 1


@pytest.mark.django_db
@override_settings(
    OTP_RESEND_COOLDOWN_SECONDS=0,
    OTP_MAX_REQUESTS_PER_WINDOW=2,
    OTP_REQUEST_WINDOW_SECONDS=900,
)
def test_request_window_limit_is_backend_authoritative():
    client = APIClient()
    assert client.post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json").status_code == 201
    assert client.post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json").status_code == 201

    response = client.post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json")
    assert response.status_code == 429
    assert response.data["error"]["code"] == "otp_rate_limited"


@pytest.mark.django_db
def test_profile_gamer_tag_is_unique_case_insensitively():
    first = User.objects.create_user(phone="09121234567")
    second = User.objects.create_user(phone="09121234568")
    PlayerProfile.objects.create(user=first, gamer_tag="SajadX")
    PlayerProfile.objects.create(user=second)

    client = APIClient()
    client.force_authenticate(second)
    response = client.patch(PROFILE_URL, {"gamer_tag": "sajadx"}, format="json")

    assert response.status_code == 400
    assert "gamer_tag" in response.data


@pytest.mark.django_db
def test_public_player_projection_does_not_leak_private_identity_fields():
    user = User.objects.create_user(phone="09121234567", email="player@example.com")
    PlayerProfile.objects.create(
        user=user,
        gamer_tag="SajadX",
        display_name="Sajad",
        city="Karaj",
        bio="Competitive player",
        interview_opt_in=True,
        avatar_key="players/example.webp",
    )

    response = APIClient().get("/api/v1/players/sajadx/")

    assert response.status_code == 200
    assert response.data["gamer_tag"] == "SajadX"
    assert "phone" not in response.data
    assert "email" not in response.data
    assert "interview_opt_in" not in response.data


@pytest.mark.django_db
def test_logout_invalidates_authenticated_session():
    client = APIClient()
    issued, delivery = request_otp(client)
    assert client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": delivery.code},
        format="json",
    ).status_code == 200

    assert client.post(LOGOUT_URL, {}, format="json").status_code == 204
    assert client.get(ME_URL).status_code in {401, 403}


@pytest.mark.django_db
def test_inactive_account_cannot_login_with_valid_otp():
    User.objects.create_user(phone="09121234567", is_active=False)
    client = APIClient()
    issued, delivery = request_otp(client)

    response = client.post(
        OTP_VERIFY_URL,
        {"challenge_id": issued.data["challenge_id"], "code": delivery.code},
        format="json",
    )

    assert response.status_code == 403
    assert response.data["error"]["code"] == "account_inactive"


@pytest.mark.django_db
@override_settings(OTP_SENDER_BACKEND="apps.accounts.otp.DisabledOtpSender")
def test_disabled_sender_fails_closed_without_burning_request_quota():
    response = APIClient().post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json")

    assert response.status_code == 503
    assert response.data["error"]["code"] == "otp_delivery_unavailable"
    challenge = OtpChallenge.objects.get()
    assert challenge.consumed_at is not None
    state = OtpRequestState.objects.get(phone="+989121234567")
    assert state.request_count == 0
    assert state.last_sent_at is None
    assert state.window_started_at is None
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_otp_request_requires_csrf_and_bootstrap_endpoint_supplies_token():
    client = APIClient(enforce_csrf_checks=True)

    rejected = client.post(OTP_REQUEST_URL, {"phone": "09121234567"}, format="json")
    assert rejected.status_code == 403

    bootstrap = client.get(CSRF_URL)
    assert bootstrap.status_code == 200
    token = bootstrap.data["csrf_token"]
    accepted = client.post(
        OTP_REQUEST_URL,
        {"phone": "09121234567"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert accepted.status_code == 201
