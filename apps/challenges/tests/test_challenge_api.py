import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.challenges import integrations, services
from apps.challenges.models import Challenge, ChallengeCommandReceipt

HUB = "/api/v1/me/challenges/"
OPPONENTS = "/api/v1/me/challenges/opponents/"
GAMES = (integrations.GameChoice(
    "ea-fc-26", "EA SPORTS FC 26", (integrations.FormatChoice("bo3", "Best of 3"),)
),)


@pytest.fixture
def players():
    users = [
        User.objects.create_user(phone=f"0912123456{i}")
        for i in range(3)
    ]
    for i, user in enumerate(users):
        PlayerProfile.objects.create(user=user, gamer_tag=f"player{i}")
    return users


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(
        integrations, "player_challenge_stats",
        lambda user: integrations.PlayerChallengeStats(30, 1500)
    )
    monkeypatch.setattr(integrations, "creation_games", lambda user: GAMES)
    monkeypatch.setattr(integrations, "match_creator_ready", lambda: True)
    monkeypatch.setattr(
        integrations, "opponent_eligible",
        lambda challenger, opponent, game_id: (
            challenger.pk != opponent.pk and opponent.is_active and game_id == "ea-fc-26"
        )
    )


def api(user, csrf=False):
    client = APIClient(enforce_csrf_checks=csrf)
    if csrf:
        client.force_login(user)
    else:
        client.force_authenticate(user=user)
    return client


def create(client, other, key="b07-create-one", **changes):
    data = {
        "opponentPlayerId": str(other.pk), "gameId": "ea-fc-26",
        "formatId": "bo3", "note": "in person",
        **changes,
    }
    return client.post(
        HUB, data, format="json", HTTP_IDEMPOTENCY_KEY=key
    )


def respond(client, challenge_id, revision, action="accept", key="b07-respond-one"):
    return client.post(
        f"{HUB}{challenge_id}/response/",
        {"revision": revision, "action": action},
        format="json", HTTP_IDEMPOTENCY_KEY=key,
    )


def cancel(client, challenge_id, revision, key="b07-cancel-one"):
    return client.post(
        f"{HUB}{challenge_id}/cancel/",
        {"revision": revision},
        format="json", HTTP_IDEMPOTENCY_KEY=key,
    )


@pytest.mark.django_db
def test_private_endpoints_and_public_identity_privacy(players, provider):
    first, second, third = players
    anonymous = APIClient()
    assert anonymous.get(HUB).status_code in (401, 403)
    assert anonymous.get(OPPONENTS, {"q": "player", "game": "ea-fc-26"}).status_code in (
        401, 403
    )
    assert anonymous.post(HUB, {}, format="json").status_code in (401, 403)
    response = api(first).get(HUB)
    assert response.status_code == 200
    assert response.data["player"]["playerId"] == str(first.pk)
    assert response.data["access"]["finalizedValidMatches"] == 30
    assert response.data["access"]["canCreate"] is True
    assert response.data["creation"]["games"][0]["formats"][0]["formatId"] == "bo3"
    search = api(first).get(OPPONENTS, {"q": "player", "game": "ea-fc-26"})
    assert search.status_code == 200
    assert search.data["outcome"] == "results"
    ids = {row["playerId"] for row in search.data["items"]}
    assert str(first.pk) not in ids
    assert ids == {str(second.pk), str(third.pk)}
    for row in search.data["items"]:
        assert set(row) == {
            "playerId", "username", "gamerTag", "avatarInitials", "challengeRating"
        }
        for private in ("phone", "email", "is_staff", "interview_opt_in"):
            assert private not in str(row)


@pytest.mark.django_db
def test_create_duplicate_active_replay_conflict_and_self_challenge(players, provider):
    first, second, _ = players
    c1 = api(first)
    original = create(c1, second)
    assert original.status_code == 200
    assert original.data["outcome"] == "accepted"
    assert create(c1, second).data == original.data
    assert Challenge.objects.count() == 1
    assert ChallengeCommandReceipt.objects.count() == 1
    duplicate = create(c1, second, key="b07-create-two")
    assert duplicate.status_code == 409
    assert duplicate.data["outcome"] == "conflict"
    backwards = create(api(second), first, key="b07-reverse-one")
    assert backwards.status_code == 409
    assert backwards.data["outcome"] == "conflict"
    same_key_diff = create(c1, second, note="changed")
    assert same_key_diff.status_code == 409
    assert same_key_diff.data["outcome"] == "conflict"
    self_request = create(c1, first, key="b07-create-self")
    assert self_request.status_code == 400
    assert self_request.data["outcome"] == "validation_error"
    assert Challenge.objects.count() == 1


@pytest.mark.django_db
def test_game_format_note_money_and_key_validation(players, provider):
    first, second, _ = players
    c1 = api(first)
    for change, field in (
        ({"gameId": "wrong"}, "game"),
        ({"formatId": "bo19"}, "format"),
        ({"note": "x" * 241}, "note"),
    ):
        result = create(c1, second, key="b07-validate-one", **change)
        assert result.status_code == 400
        assert field in result.data["fields"]
    for field in ("stake", "entryFee", "prize", "paymentUrl", "odds"):
        result = create(c1, second, key="b07-validate-one", **{field: 50})
        assert result.status_code == 400
        assert result.data["outcome"] == "validation_error"
    missing = c1.post(HUB, {
        "opponentPlayerId": str(second.pk), "gameId": "ea-fc-26",
        "formatId": "bo3",
    }, format="json")
    assert missing.status_code == 400
    assert Challenge.objects.count() == 0


@pytest.mark.django_db
def test_access_gate_and_missing_integrations_are_closed(players):
    first, second, _ = players
    page = api(first).get(HUB)
    assert page.data["access"] == {
        "unlocked": False, "canCreate": False, "challengeRating": None,
        "finalizedValidMatches": 0, "requiredFinalizedMatches": 30,
    }
    assert page.data["creation"]["games"] == []
    attempted = create(api(first), second)
    assert attempted.status_code == 404
    assert Challenge.objects.count() == 0


@pytest.mark.django_db
def test_locked_player_and_ineligible_opponent_cannot_create(players, provider, monkeypatch):
    first, second, _ = players
    monkeypatch.setattr(
        integrations, "player_challenge_stats",
        lambda user: integrations.PlayerChallengeStats(29),
    )
    response = api(first).get(HUB)
    assert response.data["access"]["unlocked"] is False
    assert response.data["access"]["canCreate"] is False
    assert create(api(first), second).status_code == 404
    monkeypatch.setattr(
        integrations, "player_challenge_stats",
        lambda user: integrations.PlayerChallengeStats(30),
    )
    monkeypatch.setattr(integrations, "opponent_eligible", lambda *args: False)
    assert create(api(first), second).status_code == 404
    assert api(first).get(OPPONENTS, {"q": "player", "game": "ea-fc-26"}).data[
        "items"
    ] == []


@pytest.mark.django_db
def test_permissions_filters_cancel_stale_and_replay(players, provider):
    first, second, intruder = players
    issued = create(api(first), second)
    challenge_id, revision = issued.data["challengeId"], issued.data["revision"]
    assert api(first).get(HUB, {"status": "outgoing"}).data["summary"]["outgoing"] == 1
    incoming = api(second).get(HUB, {"status": "incoming"}).data
    assert len(incoming["items"]) == 1
    assert incoming["items"][0]["allowedCommands"] == ["accept", "decline"]
    assert api(intruder).get(HUB).data["items"] == []
    assert respond(api(intruder), challenge_id, revision).status_code == 404
    assert cancel(api(second), challenge_id, revision).status_code == 404
    assert respond(api(first), challenge_id, revision).status_code == 404
    assert cancel(api(intruder), challenge_id, revision).status_code == 404
    assert cancel(api(first), challenge_id, str(uuid.uuid4())).data["outcome"] == "stale"
    cancelled = cancel(api(first), challenge_id, revision)
    assert cancelled.status_code == 200
    assert cancel(api(first), challenge_id, revision).data == cancelled.data
    assert cancel(api(first), challenge_id, revision, "b07-cancel-two").status_code == 409
    assert respond(api(second), challenge_id, revision).status_code == 409
    assert Challenge.objects.get(pk=challenge_id).state == Challenge.State.CANCELLED
    completed = api(second).get(HUB, {"status": "completed"}).data["items"]
    assert completed[0]["lifecycle"] == "cancelled"
    assert completed[0]["allowedCommands"] == []


@pytest.mark.django_db
def test_accept_creates_exactly_one_match_and_finalization_replay(
    players, provider, monkeypatch
):
    first, second, _ = players
    created = create(api(first), second)
    cid, revision = created.data["challengeId"], created.data["revision"]
    match_creator = Mock(return_value="match-unique-one")
    monkeypatch.setattr(integrations, "create_match_for_challenge", match_creator)
    response = respond(api(second), cid, revision)
    assert response.status_code == 200
    assert response.data["outcome"] == "accepted"
    assert respond(api(second), cid, revision).data == response.data
    assert respond(
        api(second), cid, revision, key="b07-respond-two"
    ).data["outcome"] == "stale"
    match_creator.assert_called_once()
    challenge = Challenge.objects.get(pk=cid)
    assert challenge.match_id == "match-unique-one"
    assert challenge.state == Challenge.State.ACCEPTED
    item = api(first).get(HUB, {"status": "active"}).data["items"][0]
    assert item["match"]["matchId"] == "match-unique-one"
    assert item["navigationTarget"] == {"kind": "my-matches"}
    assert item["allowedCommands"] == []

    services.record_finalized_match(
        cid, "match-unique-one", challenger_outcome="win",
        score_label="3 - 1", challenger_rating_delta=12, opponent_rating_delta=-12,
    )
    old_revision = Challenge.objects.get(pk=cid).revision
    services.record_finalized_match(
        cid, "match-unique-one", challenger_outcome="win",
        score_label="3 - 1", challenger_rating_delta=12, opponent_rating_delta=-12,
    )
    assert Challenge.objects.get(pk=cid).revision == old_revision
    with pytest.raises(ValueError, match="Conflicting"):
        services.record_finalized_match(
            cid, "match-unique-one", challenger_outcome="loss", score_label="0 - 3"
        )
    first_view = api(first).get(HUB, {"status": "completed"}).data["items"][0]
    second_view = api(second).get(HUB, {"status": "completed"}).data["items"][0]
    assert first_view["result"]["outcome"] == "win"
    assert first_view["result"]["ratingDelta"] == 12
    assert second_view["result"]["outcome"] == "loss"
    assert second_view["result"]["ratingDelta"] == -12


@pytest.mark.django_db
def test_accept_without_b08_does_not_mutate_or_store_receipt(players, provider):
    first, second, _ = players
    created = create(api(first), second)
    cid, revision = created.data["challengeId"], created.data["revision"]
    unavailable = respond(api(second), cid, revision)
    assert unavailable.status_code == 503
    assert unavailable.data["outcome"] == "unavailable"
    challenge = Challenge.objects.get(pk=cid)
    assert challenge.state == Challenge.State.PENDING
    assert challenge.match_id is None
    assert ChallengeCommandReceipt.objects.count() == 1


@pytest.mark.django_db
def test_decline_and_expiry_are_terminal_and_read_does_not_write(players, provider):
    first, second, _ = players
    created = create(api(first), second)
    cid, revision = created.data["challengeId"], created.data["revision"]
    rejected = respond(api(second), cid, revision, action="decline")
    assert rejected.status_code == 200
    assert Challenge.objects.get(pk=cid).state == Challenge.State.DECLINED
    created2 = create(api(first), second, key="b07-expire-one")
    ch = Challenge.objects.get(pk=created2.data["challengeId"])
    ch.expires_at = timezone.now() - timedelta(seconds=10)
    ch.save(update_fields=["expires_at"])
    before = ch.revision
    get = api(first).get(HUB)
    assert any(item["lifecycle"] == "invitation-expired" for item in get.data["items"])
    ch.refresh_from_db()
    assert ch.revision == before
    new = create(api(first), second, key="b07-after-expire")
    assert new.status_code == 200
    ch.refresh_from_db()
    assert ch.state == Challenge.State.EXPIRED


@pytest.mark.django_db
def test_query_validation_and_short_search(players, provider):
    first, _, _ = players
    c1 = api(first)
    for params in ({"status": "random"}, {"page": "0"}, {"page": "-2"}):
        assert c1.get(HUB, params).status_code == 400
    assert c1.get(OPPONENTS, {"q": "a", "game": "ea-fc-26"}).status_code == 400
    assert c1.get(OPPONENTS, {"q": "hello", "game": "madeup"}).status_code == 400


@pytest.mark.django_db
def test_authenticated_session_requires_csrf_for_writes(players, provider):
    first, second, _ = players
    client = api(first, csrf=True)
    payload = {
        "opponentPlayerId": str(second.pk), "gameId": "ea-fc-26",
        "formatId": "bo3", "note": "",
    }
    no_csrf = client.post(
        HUB, payload, format="json", HTTP_IDEMPOTENCY_KEY="b07-real-session"
    )
    assert no_csrf.status_code == 403
    bootstrap = client.get("/api/v1/auth/csrf/")
    assert bootstrap.status_code == 200
    yes_csrf = client.post(
        HUB, payload, format="json", HTTP_IDEMPOTENCY_KEY="b07-real-session",
        HTTP_X_CSRFTOKEN=bootstrap.data["csrf_token"],
    )
    assert yes_csrf.status_code == 200


def threaded_attempt(fn):
    close_old_connections()
    try:
        return fn()
    finally:
        close_old_connections()


@pytest.mark.django_db(transaction=True)
def test_concurrent_symmetric_create_is_unique(players, provider):
    first, second, _ = players
    barrier = threading.Barrier(2)

    def run(challenger, other, key):
        def work():
            barrier.wait(timeout=15)
            return create(api(challenger), other, key=key).status_code
        return threaded_attempt(work)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run, first, second, "b07-create-race-a")
        b = pool.submit(run, second, first, "b07-create-race-b")
        statuses = sorted([a.result(timeout=30), b.result(timeout=30)])
    assert statuses == [200, 409]
    assert Challenge.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_racing_accept_and_decline_only_one_transition(players, provider, monkeypatch):
    first, second, _ = players
    created = create(api(first), second)
    cid, revision = created.data["challengeId"], created.data["revision"]
    creator = Mock(return_value="match-only-once")
    monkeypatch.setattr(integrations, "create_match_for_challenge", creator)
    barrier = threading.Barrier(2)

    def run(action, key):
        def work():
            barrier.wait(timeout=15)
            return respond(api(second), cid, revision, action, key).status_code
        return threaded_attempt(work)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run, "accept", "b07-race-accept")
        b = pool.submit(run, "decline", "b07-race-decline")
        statuses = sorted([a.result(timeout=30), b.result(timeout=30)])
    assert statuses == [200, 409]
    challenge = Challenge.objects.get(pk=cid)
    assert challenge.state in {Challenge.State.ACCEPTED, Challenge.State.DECLINED}
    assert creator.call_count == (1 if challenge.state == Challenge.State.ACCEPTED else 0)


@pytest.mark.django_db
def test_create_idempotency_replays_after_opponent_becomes_inactive(players, provider):
    first, second, _ = players
    client = api(first)
    original = create(client, second)
    assert original.status_code == 200
    second.is_active = False
    second.save(update_fields=["is_active"])
    replay = create(client, second)
    assert replay.status_code == 200
    assert replay.data == original.data
    assert Challenge.objects.count() == 1


@pytest.mark.django_db
def test_match_finalization_cannot_precede_acceptance(players, provider):
    first, second, _ = players
    issued = create(api(first), second)
    with pytest.raises(ValueError, match="not bound"):
        services.record_finalized_match(
            issued.data["challengeId"], "unrelated-match",
            challenger_outcome="win", score_label="1 - 0",
        )
    challenge = Challenge.objects.get(pk=issued.data["challengeId"])
    assert challenge.state == Challenge.State.PENDING
    assert challenge.final_outcome == ""


@pytest.mark.django_db(transaction=True)
def test_concurrent_accept_and_cancel_cannot_both_win(players, provider, monkeypatch):
    first, second, _ = players
    issued = create(api(first), second)
    cid, revision = issued.data["challengeId"], issued.data["revision"]
    creator = Mock(return_value="match-race-safe")
    monkeypatch.setattr(integrations, "create_match_for_challenge", creator)
    barrier = threading.Barrier(2)

    def attempt(user, action, key):
        def work():
            barrier.wait(timeout=15)
            if action == "accept":
                return respond(api(user), cid, revision, action, key).status_code
            return cancel(api(user), cid, revision, key).status_code

        return threaded_attempt(work)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(attempt, second, "accept", "b07-accept-cancel-race-a")
        b = pool.submit(attempt, first, "cancel", "b07-accept-cancel-race-b")
        codes = sorted([a.result(timeout=30), b.result(timeout=30)])
    assert codes == [200, 409]
    challenge = Challenge.objects.get(pk=cid)
    assert challenge.state in {Challenge.State.ACCEPTED, Challenge.State.CANCELLED}
    assert creator.call_count == (1 if challenge.state == Challenge.State.ACCEPTED else 0)

@pytest.mark.django_db
def test_challenge_game_choices_are_real_published_b03_solo_formats(players):
    from apps.games.models import CompetitiveFormat, Game

    first, _, _ = players
    published = Game.objects.create(
        slug="approved-game", name="Approved Game", short_name="Approved",
        description="A public competitive game entry.", platforms=["PC"],
        publication_state=Game.Publication.PUBLISHED,
    )
    draft = Game.objects.create(
        slug="private-game", name="Private Game", short_name="Private",
        description="A private competitive game entry.", platforms=["PC"],
        publication_state=Game.Publication.DRAFT,
    )
    CompetitiveFormat.objects.create(
        game=published, key="solo", label="Solo", description="1v1", team_size=1
    )
    CompetitiveFormat.objects.create(
        game=published, key="team", label="Team", description="3v3", team_size=3
    )
    CompetitiveFormat.objects.create(
        game=draft, key="solo", label="Solo", description="1v1", team_size=1
    )
    response = api(first).get(HUB)
    assert response.status_code == 200
    assert response.data["access"]["canCreate"] is False
    assert response.data["creation"]["games"] == [{
        "gameId": published.id, "name": "Approved Game",
        "formats": [{"formatId": "solo", "label": "Solo"}],
    }]


@pytest.mark.django_db
def test_challenge_hub_database_pagination_keeps_virtual_expiry(players):
    first, second, _ = players
    now = timezone.now()
    rows = [
        Challenge(
            challenger=first, opponent=second,
            pair_low=min(str(first.pk), str(second.pk)),
            pair_high=max(str(first.pk), str(second.pk)),
            game_id=f"g_{i}", game_name=f"Game {i}",
            format_id="solo", format_label="Solo",
            expires_at=now + timedelta(days=1),
        ) for i in range(25)
    ]
    Challenge.objects.bulk_create(rows)
    stale = rows[0]
    stale.expires_at = now - timedelta(seconds=1)
    stale.save(update_fields=["expires_at"])
    client = api(second)
    first_page = client.get(HUB, {"status": "incoming", "page": 1})
    second_page = client.get(HUB, {"status": "incoming", "page": 2})
    assert first_page.status_code == 200
    assert first_page.data["summary"]["incoming"] == 24
    assert first_page.data["summary"]["completed"] == 1
    assert first_page.data["pagination"] == {
        "currentPage": 1, "totalPages": 2, "totalItems": 24
    }
    assert len(first_page.data["items"]) == 20
    assert len(second_page.data["items"]) == 4
    assert not (
        {item["challengeId"] for item in first_page.data["items"]}
        & {item["challengeId"] for item in second_page.data["items"]}
    )
    expired = client.get(HUB, {"status": "completed"})
    assert expired.data["items"][0]["lifecycle"] == "invitation-expired"
    stale.refresh_from_db()
    assert stale.state == Challenge.State.PENDING

@pytest.mark.django_db
def test_authoritative_thirty_finalizations_unlock_but_no_implicit_schedule(players):
    from apps.games.models import CompetitiveFormat, Game
    from apps.matches.services import advance_match, create_match_for_source
    from apps.results.models import FinalizedResultEvent
    from apps.results.services import confirm_score, submit_score

    challenger, opponent, _ = players
    game = Game.objects.create(
        slug="b07-verified-game", name="Verified Game", short_name="Verified",
        description="A real published game for finalized B08 acceptance tests.",
        platforms=["PC"], publication_state=Game.Publication.PUBLISHED,
    )
    CompetitiveFormat.objects.create(
        game=game, key="solo", label="Solo", description="1v1", team_size=1
    )
    for number in range(30):
        match = create_match_for_source(
            source_kind="tournament", source_id=f"verified-final-{number}",
            participant_a=challenger, participant_b=opponent,
            game_id=game.pk, game_name=game.name,
            competition_title="Verified free tournament",
            starts_at=timezone.now() - timedelta(hours=1),
        )
        advance_match(match.pk, "ready")
        advance_match(match.pk, "awaiting-result")
        match.refresh_from_db()
        result = submit_score(
            match.pk, challenger, str(match.revision), 3, 1,
            f"b07-real-score-{number}",
        )
        assert result["outcome"] == "accepted"
        match.refresh_from_db()
        finalized = confirm_score(
            match.pk, opponent, str(match.revision), 1, 3
        )
        assert finalized["outcome"] == "finalized"
    assert FinalizedResultEvent.objects.count() == 30
    stats = integrations.player_challenge_stats(challenger)
    assert stats.finalized_valid_matches == 30
    assert stats.challenge_rating is None  # no fabricated B09 rating/season
    access = services.access(challenger)
    assert access["unlocked"] is True
    assert access["finalizedValidMatches"] == 30
    assert access["canCreate"] is False  # scheduling contract deliberately unresolved
    assert integrations.opponent_eligible(challenger, opponent, game.pk)
    blocked = create(api(challenger), opponent, key="b07-real-locked",
                     gameId=game.pk, formatId="solo")
    assert blocked.data["outcome"] == "unavailable"
    assert Challenge.objects.count() == 0
