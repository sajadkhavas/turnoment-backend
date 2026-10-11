from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import IntegrityError, connections, transaction
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.achievements.models import (
    AchievementCategory, AchievementDefinition, AchievementProgress,
    AchievementProgressEvent,
)
from apps.achievements.services import record_progress

URL = "/api/v1/me/achievements/"


def user(num):
    account = User.objects.create_user(phone=f"0935{num:07d}")
    PlayerProfile.objects.create(user=account, gamer_tag=f"Hero{num:07d}")
    return account


def client(account):
    c = APIClient()
    c.force_authenticate(account)
    return c


def make_defs():
    a = AchievementCategory.objects.create(id="competitive", name="Competitive")
    b = AchievementCategory.objects.create(id="consistency", name="Consistency")
    first = AchievementDefinition.objects.create(
        category=a, code="first_step", title="First step",
        description="A verified first step.", target=1, is_published=True,
    )
    second = AchievementDefinition.objects.create(
        category=b, code="steady_path", title="Steady path",
        description="A verified continued path.", target=4, has_progress=True,
        is_published=True,
    )
    hidden = AchievementDefinition.objects.create(
        category=b, code="private", title="Private",
        description="Not published.", target=1, is_published=False,
    )
    return first, second, hidden


@pytest.mark.django_db
def test_private_hub_empty_and_no_fabricated_awards():
    actor = user(1)
    denied = APIClient().get(URL)
    assert denied.status_code in (401, 403)
    payload = client(actor).get(URL).data
    assert payload["player"]["playerId"] == str(actor.pk)
    assert payload["timezone"] == "Asia/Tehran"
    assert payload["summary"] == {
        "total": 0, "unlocked": 0, "inProgress": 0, "locked": 0
    }
    assert payload["items"] == []
    assert payload["pagination"] == {
        "currentPage": 1, "totalPages": 1, "totalItems": 0
    }


@pytest.mark.django_db
def test_progress_status_summary_filters_order_and_no_other_player_data():
    actor, other = user(2), user(3)
    first, second, hidden = make_defs()
    assert client(actor).get(URL).data["summary"] == {
        "total": 2, "unlocked": 0, "inProgress": 0, "locked": 2
    }
    record_progress(user=other, definition_id=first.pk, event_key="other-event")
    record_progress(user=actor, definition_id=second.pk, event_key="round-1")
    state = client(actor).get(URL).data
    assert state["summary"] == {
        "total": 2, "unlocked": 0, "inProgress": 1, "locked": 1
    }
    assert state["categories"] == [
        {"categoryId": "competitive", "name": "Competitive"},
        {"categoryId": "consistency", "name": "Consistency"},
    ]
    assert [item["status"] for item in state["items"]] == ["locked", "in-progress"]
    assert state["items"][1]["progress"] == {"current": 1, "target": 4, "percent": 25}
    assert state["items"][1]["unlockedAt"] is None
    assert "phone" not in str(state)
    assert "private" not in str(state)
    filtered = client(actor).get(URL, {"status": "in-progress",
                                      "category": "consistency"}).data
    assert filtered["pagination"]["totalItems"] == 1
    assert filtered["summary"]["total"] == 2
    assert filtered["items"][0]["code"] == "steady_path"
    record_progress(user=actor, definition_id=second.pk, event_key="round-2", increment=9)
    record_progress(user=actor, definition_id=first.pk, event_key="first-event")
    unlocked = client(actor).get(URL, {"status": "unlocked", "sort": "recent"}).data
    assert unlocked["summary"]["unlocked"] == 2
    assert len(unlocked["items"]) == 2
    for item in unlocked["items"]:
        assert item["unlockedAt"].endswith("+00:00")
        if item["progress"]:
            assert item["progress"] == {"current": 4, "target": 4, "percent": 100}
    assert client(other).get(URL, {"status": "unlocked"}).data[
        "pagination"
    ]["totalItems"] == 1


@pytest.mark.django_db
def test_query_rejection_finite_pagination_and_read_only():
    actor = user(4)
    first, second, _ = make_defs()
    for query in (
        {"status": "owned"}, {"sort": "name"}, {"category": "!"},
        {"page": "0"}, {"page": "nonsense"}, {"mystery": "hello"},
    ):
        assert client(actor).get(URL, query).status_code == 400
    assert client(actor).get(URL + "?sort=recent&sort=progress").status_code == 400
    assert client(actor).post(URL, {"code": "self-award"}, format="json").status_code == 405
    assert client(actor).get(URL, {"page": "88"}).data[
        "pagination"
    ]["currentPage"] == 1
    assert not AchievementProgress.objects.filter(user=actor).exists()
    assert {i["code"] for i in client(actor).get(URL).data["items"]} == {
        first.code, second.code
    }


@pytest.mark.django_db
def test_replayed_event_is_idempotent_and_capped():
    actor = user(5)
    first, second, hidden = make_defs()
    current = record_progress(user=actor, definition_id=second.pk, event_key="event-1",
                              increment=2)
    again = record_progress(user=actor, definition_id=second.pk, event_key="event-1",
                            increment=3)
    assert current.pk == again.pk
    assert again.current == 2
    completed = record_progress(user=actor, definition_id=second.pk,
                                event_key="event-2", increment=9)
    assert completed.current == 4
    assert completed.unlocked_at is not None
    original_time = completed.unlocked_at
    assert record_progress(user=actor, definition_id=second.pk, event_key="event-3"
                           ).unlocked_at == original_time
    assert AchievementProgressEvent.objects.filter(
        user=actor, definition=second
    ).count() == 3
    with pytest.raises(AchievementDefinition.DoesNotExist):
        record_progress(user=actor, definition_id=hidden.pk, event_key="hidden")
    for key, inc in (("invalid space", 1), ("bad", 0), ("bad", True)):
        with pytest.raises(ValueError):
            record_progress(user=actor, definition_id=first.pk,
                            event_key=key, increment=inc)


@pytest.mark.django_db
def test_constraints_prevent_duplicate_event_progress_and_invalid_definition():
    actor = user(6)
    first, second, _ = make_defs()
    record_progress(user=actor, definition_id=first.pk, event_key="event")
    with pytest.raises(IntegrityError), transaction.atomic():
        AchievementProgressEvent.objects.create(
            user=actor, definition=first, event_key="event"
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        AchievementProgress.objects.create(
            user=actor, definition=first, current=0
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        AchievementDefinition.objects.create(
            category=first.category, code="no_target", title="No target",
            description="Invalid", target=0, has_progress=True
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        AchievementDefinition.objects.create(
            category=second.category, code="bad_binary", title="Bad binary",
            description="Invalid", target=2, has_progress=False
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_event_delivered_once():
    actor = user(7)
    first, second, _ = make_defs()

    def run(_):
        connections.close_all()
        try:
            return record_progress(
                user=actor, definition_id=second.pk,
                event_key="same-game-unique-id", increment=1
            ).current
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, range(2))) == [1, 1]
    assert AchievementProgressEvent.objects.filter(
        user=actor, definition=second
    ).count() == 1
    assert AchievementProgress.objects.get(
        user=actor, definition=second
    ).current == 1
