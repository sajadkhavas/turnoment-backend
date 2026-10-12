"""B99 backend API acceptance across real B03/B07/B08/B09/B02 records.

APIClient sessions keep separate cookies and CSRF protections. Browser
Playwright acceptance is a separate explicit gate, not claimed by these tests.
"""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.challenges.models import Challenge
from apps.games.models import CompetitiveFormat, Game
from apps.gaming_centers.models import City
from apps.matches.models import Match
from apps.matches.services import advance_match, create_match_for_source
from apps.rankings.models import AppliedMatchEvent, PlayerRating, PublicRankingIdentity, Season
from apps.results.models import FinalizedResultEvent
from apps.results.services import confirm_score, submit_score


def session(user):
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    return client, response.data["csrf_token"]


@pytest.mark.django_db
def test_two_session_real_challenge_to_finalized_ranking_and_dashboard():
    a, b, stranger = [
        User.objects.create_user(phone=f"0912222333{number}")
        for number in range(3)
    ]
    for user, tag in ((a, "alpha99"), (b, "bravo99"), (stranger, "third99")):
        PlayerProfile.objects.create(user=user, gamer_tag=tag)
    game = Game.objects.create(
        slug="b99-verified-game", name="B99 Verified Game", short_name="B99",
        description="Real published game for B99 cross-domain acceptance.",
        platforms=["PC"], publication_state=Game.Publication.PUBLISHED,
    )
    CompetitiveFormat.objects.create(
        game=game, key="solo", label="Solo", description="One on one", team_size=1,
    )
    season = Season.objects.create(
        slug="b99-acceptance", label="B99 acceptance season",
        starts_at=timezone.now() - timedelta(days=1),
        ends_at=timezone.now() + timedelta(days=1),
        is_published=True,
    )
    city = City.objects.create(slug="karaj", name="Karaj")
    for user, handle in ((a, "alpha_b99"), (b, "bravo_b99")):
        PublicRankingIdentity.objects.create(
            user=user, city=city, username=handle, is_published=True,
            search_visibility="indexable",
        )

    # The B07 eligibility gate requires 30 genuinely finalized B08 matches.
    for number in range(30):
        old = create_match_for_source(
            source_kind="tournament", source_id=f"b99-free-seed-{number}",
            participant_a=a, participant_b=b,
            game_id=game.pk, game_name=game.name,
            competition_title="B99 free eligibility games",
            starts_at=timezone.now() - timedelta(hours=1),
        )
        advance_match(old.pk, "ready")
        advance_match(old.pk, "awaiting-result")
        old.refresh_from_db()
        result = submit_score(
            old.pk, a, str(old.revision), 3, 1, f"b99-seed-score-{number}",
        )
        assert result["outcome"] == "accepted"
        old.refresh_from_db()
        assert confirm_score(
            old.pk, b, str(old.revision), 1, 3
        )["outcome"] == "finalized"
    assert FinalizedResultEvent.objects.count() == 30

    client_a, token_a = session(a)
    client_b, token_b = session(b)
    client_stranger, _ = session(stranger)
    hub = "/api/v1/me/challenges/"
    access = client_a.get(hub)
    assert access.status_code == 200
    assert access.data["access"]["canCreate"] is True
    discovery = client_a.get(
        hub + "opponents/", {"q": "bravo", "game": game.pk},
    )
    assert discovery.status_code == 200
    assert [item["playerId"] for item in discovery.data["items"]] == [str(b.pk)]
    assert "phone" not in str(discovery.data)

    request = {
        "opponentPlayerId": str(b.pk), "gameId": game.pk,
        "formatId": "solo", "note": "In-person free game",
    }
    assert client_a.post(
        hub, request, format="json", HTTP_IDEMPOTENCY_KEY="b99-create-challenge"
    ).status_code == 403
    created = client_a.post(
        hub, request, format="json", HTTP_IDEMPOTENCY_KEY="b99-create-challenge",
        HTTP_X_CSRFTOKEN=token_a,
    )
    assert created.status_code == 200
    assert created.data["outcome"] == "accepted"
    challenge_id = created.data["challengeId"]
    assert client_b.get(hub, {"status": "incoming"}).data["summary"]["incoming"] == 1
    response_url = f"{hub}{challenge_id}/response/"
    command = {"revision": created.data["revision"], "action": "accept"}
    assert client_stranger.post(
        response_url, command, format="json",
        HTTP_IDEMPOTENCY_KEY="b99-outsider-response",
    ).status_code in (403, 404)
    accepted = client_b.post(
        response_url, command, format="json",
        HTTP_IDEMPOTENCY_KEY="b99-accept-challenge",
        HTTP_X_CSRFTOKEN=token_b,
    )
    assert accepted.status_code == 200
    replay = client_b.post(
        response_url, command, format="json",
        HTTP_IDEMPOTENCY_KEY="b99-accept-challenge",
        HTTP_X_CSRFTOKEN=token_b,
    )
    assert replay.data == accepted.data
    match = Match.objects.get(source_kind="challenge", source_id=challenge_id)
    assert Match.objects.filter(source_kind="challenge", source_id=challenge_id).count() == 1
    assert str(match.pk) == Challenge.objects.get(pk=challenge_id).match_id
    assert client_stranger.get(
        f"/api/v1/matches/{match.pk}/result/"
    ).status_code == 404

    advance_match(match.pk, "awaiting-result")
    result_url = f"/api/v1/matches/{match.pk}/result/"
    revision = client_a.get(result_url).data["revision"]
    submitted = client_a.post(
        result_url,
        {"revision": revision, "playerScore": 4, "opponentScore": 2},
        format="json", HTTP_X_CSRFTOKEN=token_a,
        HTTP_IDEMPOTENCY_KEY="b99-real-score-1",
    )
    assert submitted.status_code == 200
    assert submitted.data["outcome"] == "accepted"
    revision = client_b.get(result_url).data["revision"]
    confirmed = client_b.post(
        result_url + "confirm/",
        {"revision": revision, "playerScore": 2, "opponentScore": 4},
        format="json", HTTP_X_CSRFTOKEN=token_b,
    )
    assert confirmed.status_code == 200
    assert confirmed.data["outcome"] == "finalized"
    assert FinalizedResultEvent.objects.filter(match=match).count() == 1
    assert Challenge.objects.get(pk=challenge_id).state == Challenge.State.COMPLETED

    # A real operator command consumes all 31 durable events chronologically.
    output = StringIO()
    call_command("drain_b08_events", "--limit", "100", stdout=output)
    assert "Applied 31 B08 events." in output.getvalue()
    assert AppliedMatchEvent.objects.count() == 31
    assert PlayerRating.objects.get(
        user=a, game=game, season=season, kind="challenge"
    ).rating == 1016
    assert PlayerRating.objects.get(
        user=b, game=game, season=season, kind="challenge"
    ).rating == 984
    second_run = StringIO()
    call_command("drain_b08_events", stdout=second_run)
    assert "Applied 0 B08 events." in second_run.getvalue()
    assert AppliedMatchEvent.objects.count() == 31

    ranking = APIClient().get(
        "/api/v1/rankings/",
        {"game": game.slug, "season": season.slug, "type": "challenge"},
    )
    assert ranking.status_code == 200
    assert [item["rating"] for item in ranking.data["items"]] == [1016, 984]
    assert [item["username"] for item in ranking.data["items"]] == [
        "alpha_b99", "bravo_b99",
    ]
    dashboard_a = client_a.get("/api/v1/me/dashboard/")
    dashboard_b = client_b.get("/api/v1/me/dashboard/")
    assert dashboard_a.status_code == dashboard_b.status_code == 200
    assert dashboard_a.data["snapshot"]["finalizedMatches"] == 31
    assert dashboard_b.data["snapshot"]["finalizedMatches"] == 31
    assert dashboard_a.data["snapshot"]["challengeRating"] == 1016
    assert dashboard_b.data["snapshot"]["challengeRating"] == 984
    assert client_stranger.get("/api/v1/me/dashboard/").data["snapshot"][
        "finalizedMatches"
    ] == 0
    assert "091222233" not in str(ranking.data)
    assert "091222233" not in str(dashboard_a.data)

    repeated_confirmation = client_b.post(
        result_url + "confirm/",
        {"revision": revision, "playerScore": 2, "opponentScore": 4},
        format="json", HTTP_X_CSRFTOKEN=token_b,
    )
    assert repeated_confirmation.data["outcome"] == "already_finalized"
    assert AppliedMatchEvent.objects.count() == 31


@pytest.mark.django_db
def test_ranking_drain_fails_closed_without_configured_season():
    a = User.objects.create_user(phone="09120000001")
    b = User.objects.create_user(phone="09120000002")
    game = Game.objects.create(
        slug="b99-no-season", name="No season", short_name="No season",
        description="Published game without configured ranking season.",
        platforms=["PC"], publication_state=Game.Publication.PUBLISHED,
    )
    match = create_match_for_source(
        source_kind="challenge", source_id="b99-no-season-fixture",
        participant_a=a, participant_b=b, game_id=game.pk, game_name=game.name,
        competition_title="Free challenge", starts_at=timezone.now(),
    )
    advance_match(match.pk, "ready")
    advance_match(match.pk, "awaiting-result")
    match.refresh_from_db()
    submit_score(match.pk, a, str(match.revision), 1, 0, "b99-no-season-score")
    match.refresh_from_db()
    assert confirm_score(
        match.pk, b, str(match.revision), 0, 1
    )["outcome"] == "finalized"
    with pytest.raises(CommandError, match="Ranking drain blocked"):
        call_command("drain_b08_events")
    assert AppliedMatchEvent.objects.count() == 0


@pytest.mark.django_db
def test_b99_database_refuses_ambiguous_overlapping_seasons():
    """Even unpublished seasons cannot silently hijack B08 ranking attribution."""
    from django.db import IntegrityError, transaction

    now = timezone.now()
    Season.objects.create(
        slug="b99-first-window", label="First window",
        starts_at=now - timedelta(days=1), ends_at=now,
    )
    # Adjacent [start, end) seasons are valid and deterministic.
    Season.objects.create(
        slug="b99-adjacent-window", label="Adjacent window",
        starts_at=now, ends_at=now + timedelta(days=1),
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Season.objects.create(
            slug="b99-ambiguous-window", label="Ambiguous overlap",
            starts_at=now - timedelta(hours=1), ends_at=now + timedelta(hours=1),
        )
    assert Season.objects.count() == 2


@pytest.mark.django_db
def test_b99_scheduler_is_explicitly_opt_in_and_empty_drain_is_safe():
    from django.conf import settings

    from apps.rankings.tasks import drain_verified_b08

    assert not settings.B99_ENABLE_RANKING_DRAIN
    assert settings.CELERY_BEAT_SCHEDULE == {}
    result = drain_verified_b08(limit=100)
    assert result == {"applied": 0, "skipped": None}
    assert AppliedMatchEvent.objects.count() == 0
