import base64
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.matches.services import advance_match, create_match_for_source
from apps.notifications.delivery import dispatch_one
from apps.notifications.events import notify
from apps.notifications.models import Notification, NotificationDelivery, PushSubscription
from apps.notifications.push_api import valid_subscription
from apps.results.services import submit_score


def subscription():
    encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode()  # noqa: E731
    return {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-device",
        "keys": {"p256dh": encode(b"\x04" + b"x" * 64), "auth": encode(b"a" * 16)},
    }


def test_push_endpoint_validation_blocks_private_hosts():
    data = subscription()
    assert valid_subscription(data)
    for endpoint in (
        "http://fcm.googleapis.com/x",
        "https://127.0.0.1/x",
        "https://fcm.googleapis.com.evil.test/x",
        "https://user@fcm.googleapis.com/x",
    ):
        assert not valid_subscription({**data, "endpoint": endpoint})
    assert not valid_subscription({**data, "keys": {"p256dh": "invalid", "auth": "invalid"}})


@pytest.mark.django_db
def test_subscription_ownership_csrf_and_disabled_sms():
    a = User.objects.create_user(phone="09121111001")
    b = User.objects.create_user(phone="09121111002")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(a)
    url = "/api/v1/me/notifications/push/subscription/"
    data = subscription()
    assert client.post(url, data, format="json").status_code == 403
    csrf = client.get("/api/v1/auth/csrf/").data["csrf_token"]
    assert client.post(url, data, format="json", HTTP_X_CSRFTOKEN=csrf).status_code == 200
    client.force_authenticate(user=b)
    assert client.post(url, data, format="json").status_code == 409
    client.delete(url, {"endpoint": data["endpoint"]}, format="json")
    assert PushSubscription.objects.get().active
    notify([a.pk], "test-sms-disabled", "system", "Test", "Message")
    NotificationDelivery.objects.filter(channel="push").delete()
    assert dispatch_one()
    item = NotificationDelivery.objects.get()
    assert item.state == "disabled"
    assert item.sent_at is None


@pytest.mark.django_db
def test_domain_notifications_are_private_replay_safe_and_transactional():
    a = User.objects.create_user(phone="09121111003")
    b = User.objects.create_user(phone="09121111004")
    match = create_match_for_source(
        source_kind="challenge",
        source_id="test-notify",
        participant_a=a,
        participant_b=b,
        game_id="fc",
        game_name="FC",
        competition_title="Test",
        starts_at=timezone.now(),
    )
    match = advance_match(match.pk, "ready")
    assert Notification.objects.filter(event_key=f"match-{match.pk}-ready").count() == 2
    advance_match(match.pk, "ready")
    assert Notification.objects.filter(event_key=f"match-{match.pk}-ready").count() == 2
    match = advance_match(match.pk, "awaiting-result")
    submit_score(match.pk, a, str(match.revision), 3, 1, "notify-submit-1")
    reported = Notification.objects.filter(title="نتیجه بازی نیاز به تأیید تو دارد")
    assert reported.count() == 1
    assert reported.get().recipient_id == b.pk
    with pytest.raises(RuntimeError), transaction.atomic():
        notify([a.pk], "rollback-notify", "system", "Test", "Message")
        raise RuntimeError("Rollback")
    assert not Notification.objects.filter(event_key="rollback-notify").exists()


@pytest.mark.django_db
def test_failed_push_keeps_retry_without_exposing_exception(settings):
    settings.PUSH_VAPID_PRIVATE_KEY = "test-key"
    settings.PUSH_VAPID_SUBJECT = "mailto:test@example.test"
    a = User.objects.create_user(phone="09121111005")
    data = subscription()
    PushSubscription.objects.create(recipient=a, endpoint=data["endpoint"], **data["keys"])
    notify([a.pk], "push-retry-test", "system", "Test", "Message")
    NotificationDelivery.objects.filter(channel="sms").delete()
    with patch("pywebpush.webpush", side_effect=RuntimeError("private-token")):
        assert dispatch_one()
    item = NotificationDelivery.objects.get()
    assert item.state == "retry" and item.attempts == 1
    assert item.next_attempt_at > timezone.now() - timedelta(seconds=1)
    assert item.last_error == "provider_failed" and item.sent_at is None


@pytest.mark.django_db
def test_logout_revokes_push_endpoints_without_touching_other_users():
    # A service worker can keep receiving push after the session cookie is
    # removed. Fail closed on logout, including deliveries queued earlier.
    a = User.objects.create_user(phone="09121111006")
    b = User.objects.create_user(phone="09121111007")
    data = subscription()
    other_endpoint = "https://fcm.googleapis.com/fcm/send/other-device"
    b_endpoint = "https://fcm.googleapis.com/fcm/send/unrelated-device"
    for endpoint in (data["endpoint"], other_endpoint):
        PushSubscription.objects.create(recipient=a, endpoint=endpoint, **data["keys"])
    PushSubscription.objects.create(recipient=b, endpoint=b_endpoint, **data["keys"])
    notify([a.pk], "logout-privacy", "system", "Private", "Sensitive")
    NotificationDelivery.objects.filter(channel="sms").delete()
    assert NotificationDelivery.objects.filter(channel="push", state="pending").count() == 2

    client = APIClient(enforce_csrf_checks=True)
    client.force_login(a)
    assert client.post("/api/v1/auth/logout/").status_code == 403
    assert PushSubscription.objects.filter(recipient=a, active=True).count() == 2
    csrf = client.get("/api/v1/auth/csrf/").data["csrf_token"]
    assert client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=csrf).status_code == 204
    assert not PushSubscription.objects.filter(recipient=a, active=True).exists()
    assert PushSubscription.objects.filter(recipient=b, active=True).count() == 1
    assert client.get("/api/v1/auth/me/").status_code in (401, 403)

    assert dispatch_one() and dispatch_one()
    assert not dispatch_one()
    assert NotificationDelivery.objects.filter(channel="push", state="expired").count() == 2
    notify([a.pk], "logout-new-event", "system", "Private", "Later")
    assert not NotificationDelivery.objects.filter(
        notification__event_key="logout-new-event", channel="push"
    ).exists()
