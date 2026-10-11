from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import emit_notification, mark_one_read


def user(phone):
    return User.objects.create_user(phone=phone)


@pytest.mark.django_db
def test_inbox_filters_pagination_and_foreign_read_privacy():
    alice = user("+989121111111")
    bob = user("+989122222222")
    for i in range(7):
        emit_notification(
            recipient_id=alice.pk, event_key=f"match-{i}", kind="match",
            title=f"Match {i}", body="Test notification body",
            target_kind="my-matches",
        )
    alien, _ = emit_notification(
        recipient_id=bob.pk, event_key="foreign", kind="account",
        title="Private", body="Private data",
    )
    client = APIClient()
    assert client.get("/api/v1/me/notifications/").status_code == 403
    client.force_authenticate(user=alice)
    response = client.get("/api/v1/me/notifications/")
    assert response.status_code == 200
    assert response.data["summary"] == {"total": 7, "unread": 7}
    assert len(response.data["items"]) == 5
    assert response.data["pagination"] == {"currentPage": 1, "totalPages": 2, "totalItems": 7}
    second = client.get("/api/v1/me/notifications/?page=2")
    assert len(second.data["items"]) == 2
    assert client.get("/api/v1/me/notifications/?state=read").data["pagination"]["totalItems"] == 0
    assert client.get("/api/v1/me/notifications/?kind=challenge").data["items"] == []
    assert client.get("/api/v1/me/notifications/?page=0").status_code == 400
    assert client.get("/api/v1/me/notifications/?kind=invalid").status_code == 400
    assert client.get("/api/v1/me/notifications/?evil=1").status_code == 400
    assert client.post(
        f"/api/v1/me/notifications/{alien.pk}/read/", {}, format="json"
    ).status_code == 404
    assert client.get("/api/v1/me/notifications/").data["summary"]["unread"] == 7


@pytest.mark.django_db
def test_read_one_all_replay_and_target_contract():
    alice = user("+989123333333")
    first, created = emit_notification(
        recipient_id=alice.pk, event_key="result-1", kind="match",
        title="Result is ready", body="Open the match result",
        target_kind="result-submission", target_id="m-204",
    )
    assert created
    same, created = emit_notification(
        recipient_id=alice.pk, event_key="result-1", kind="match",
        title="Result is ready", body="Open the match result",
        target_kind="result-submission", target_id="m-204",
    )
    assert not created and first.id == same.id
    with pytest.raises(ValueError):
        emit_notification(
            recipient_id=alice.pk, event_key="result-1", kind="match",
            title="CHANGED", body="Open the match result",
        )
    for i in range(2):
        emit_notification(
            recipient_id=alice.pk, event_key=f"event-{i}", kind="system",
            title="System", body="An update",
        )
    client = APIClient()
    client.force_authenticate(user=alice)
    entry = client.get("/api/v1/me/notifications/?kind=match").data["items"][0]
    assert entry["target"] == {"kind": "result-submission", "matchId": "m-204"}
    one_url = f"/api/v1/me/notifications/{first.pk}/read/"
    first_response = client.post(one_url, {}, format="json")
    assert first_response.status_code == 200
    assert first_response.data["outcome"] == "saved"
    assert first_response.data["unreadCount"] == 2
    assert client.post(one_url, {}, format="json").data["readAt"] == first_response.data["readAt"]
    all_response = client.post("/api/v1/me/notifications/read-all/", {}, format="json")
    assert all_response.data["markedCount"] == 2
    assert all_response.data["unreadCount"] == 0
    assert client.post(
        "/api/v1/me/notifications/read-all/", {}, format="json"
    ).data["markedCount"] == 0
    assert Notification.objects.filter(recipient=alice, read_at__isnull=True).count() == 0
    assert client.get("/api/v1/me/notifications/?state=read").data["pagination"]["totalItems"] == 3


@pytest.mark.django_db
def test_reject_invalid_target_and_empty_content():
    alice = user("+989124444444")
    with pytest.raises(ValidationError):
        emit_notification(
            recipient_id=alice.pk, event_key="bad", kind="system",
            title="", body="contents", target_kind="tournament-detail",
            target_id="https://evil.com",
        )
    assert Notification.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_replay_produces_exactly_one_row():
    alice = user("+989125555555")

    def submit(_):
        close_old_connections()
        try:
            return emit_notification(
                recipient_id=alice.pk, event_key="same-event", kind="match",
                title="Match", body="Match update",
            )[0].pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        ids = list(pool.map(submit, range(3)))
    assert len(set(ids)) == 1
    assert Notification.objects.filter(recipient=alice).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_read_once_does_not_double_decrement():
    alice = user("+989126666666")
    item, _ = emit_notification(
        recipient_id=alice.pk, event_key="read", kind="system", title="T", body="Body",
    )

    def read(_):
        close_old_connections()
        try:
            return mark_one_read(recipient_id=alice.pk, notification_id=item.pk)[1]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        counts = list(pool.map(read, range(2)))
    assert counts == [0, 0]
    assert Notification.objects.get(pk=item.pk).read_at is not None
