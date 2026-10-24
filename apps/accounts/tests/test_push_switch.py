"""Regression coverage for stale WebPush endpoints on OTP account switching."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.otp import MemoryOtpSender
from apps.notifications.delivery import dispatch_one
from apps.notifications.events import notify
from apps.notifications.models import NotificationDelivery, PushSubscription


def issue_otp(client, phone):
    MemoryOtpSender.clear()
    response = client.post("/api/v1/auth/otp/request/", {"phone": phone}, format="json")
    assert response.status_code == 201
    return response.data["challenge_id"], MemoryOtpSender.outbox[-1].code


def verify_otp(client, challenge_id, code):
    return client.post(
        "/api/v1/auth/otp/verify/",
        {"challenge_id": challenge_id, "code": code},
        format="json",
    )


def subscribe(user, endpoint):
    return PushSubscription.objects.create(
        recipient=user, endpoint=endpoint, p256dh="test-public-key", auth="test-auth"
    )


@pytest.mark.django_db
def test_switching_accounts_revokes_previous_push_and_queued_private_delivery():
    old = User.objects.create_user(phone="09121111221")
    new = User.objects.create_user(phone="09121111222")
    old_sub = subscribe(old, "https://fcm.googleapis.com/fcm/send/old-switch-device")
    new_sub = subscribe(new, "https://fcm.googleapis.com/fcm/send/new-switch-device")
    notify([old.pk], "otp-switch-old-private", "system", "Private", "Old account")
    NotificationDelivery.objects.filter(channel="sms").delete()
    assert NotificationDelivery.objects.filter(
        channel="push", subscription=old_sub, state="pending"
    ).count() == 1

    client = APIClient()
    client.force_login(old)
    challenge_id, code = issue_otp(client, "09121111222")
    response = verify_otp(client, challenge_id, code)
    assert response.status_code == 200
    assert response.data["id"] == str(new.pk)
    assert client.get("/api/v1/auth/me/").data["id"] == str(new.pk)

    old_sub.refresh_from_db()
    new_sub.refresh_from_db()
    assert old_sub.active is False
    assert new_sub.active is True
    assert dispatch_one() is True
    assert NotificationDelivery.objects.get(
        channel="push", subscription=old_sub
    ).state == "expired"
    notify([old.pk], "otp-switch-after", "system", "Private", "Later")
    assert not NotificationDelivery.objects.filter(
        notification__event_key="otp-switch-after", channel="push"
    ).exists()


@pytest.mark.django_db
def test_failed_or_same_account_otp_does_not_revoke_push():
    user = User.objects.create_user(phone="09121111223")
    sub = subscribe(user, "https://fcm.googleapis.com/fcm/send/same-account-device")
    client = APIClient()
    client.force_login(user)
    challenge_id, code = issue_otp(client, "09121111223")
    wrong = "000000" if code != "000000" else "111111"
    assert verify_otp(client, challenge_id, wrong).status_code == 400
    sub.refresh_from_db()
    assert sub.active is True

    assert verify_otp(client, challenge_id, code).status_code == 200
    sub.refresh_from_db()
    assert sub.active is True
    assert client.get("/api/v1/auth/me/").data["id"] == str(user.pk)
