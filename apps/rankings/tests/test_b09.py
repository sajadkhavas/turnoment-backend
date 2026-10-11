import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.games.models import Game
from apps.gaming_centers.models import City
from apps.rankings.models import (
    AppliedMatchEvent,
    PlayerRating,
    PublicRankingIdentity,
    Season,
)
from apps.rankings.services import (
    FinalizedInput,
    apply_verified_finalization,
    elo_delta,
)


@pytest.fixture
def competitive_setup():
    game = Game.objects.create(
        id="g_fifa", slug="ea-fc", name="EA FC", short_name="EA",
        description="Competitive football game for registered gaming centers.",
        platforms=["PC"], publication_state="published",
    )
    season = Season.objects.create(
        slug="autumn-2026", label="Autumn 2026",
        starts_at=timezone.now() - timedelta(days=30),
        ends_at=timezone.now() + timedelta(days=30), is_published=True,
    )
    city = City.objects.create(slug="karaj", name="Karaj")
    users = [
        User.objects.create_user(phone=f"09121230{i:03d}")
        for i in range(3)
    ]
    for i, user in enumerate(users):
        PlayerProfile.objects.create(user=user, gamer_tag=f"Gamer{i}")
        PublicRankingIdentity.objects.create(
            user=user, city=city, username=f"gamer_{i}", is_published=True,
            search_visibility="indexable",
        )
    return game, season, city, users


def payload(setup, *, event_id=None, match_id=None, a=0, b=1, kind="tournament",
            score_a=3, score_b=1, at=None):
    game, _, _, users = setup
    return FinalizedInput(
        event_id=event_id or uuid.uuid4(),
        match_id=match_id or uuid.uuid4(),
        player_a_id=users[a].pk, player_b_id=users[b].pk,
        game_id=game.pk, kind=kind, source_id=str(uuid.uuid4()),
        competition_title="Free cup", timezone="Asia/Tehran",
        score_a=score_a, score_b=score_b, finalized_at=at or timezone.now(),
    )


@pytest.mark.django_db
def test_deterministic_elo_and_exactly_once_replay(competitive_setup):
    setup = competitive_setup
    event = payload(setup)
    assert elo_delta(1000, 1000, 3, 1) == 16
    assert elo_delta(1000, 1000, 0, 1) == -16
    assert elo_delta(1000, 1000, 1, 1) == 0
    first, created = apply_verified_finalization(event)
    assert created
    repeat, created = apply_verified_finalization(event)
    assert not created and repeat.pk == first.pk
    a, b = setup[-1][:2]
    ra = PlayerRating.objects.get(user=a)
    rb = PlayerRating.objects.get(user=b)
    assert (ra.rating, ra.played, ra.wins) == (1016, 1, 1)
    assert (rb.rating, rb.played, rb.losses) == (984, 1, 1)
    assert AppliedMatchEvent.objects.count() == 1
    assert PlayerRating.objects.count() == 2


@pytest.mark.django_db
def test_replay_conflict_and_reuse_match_identity_rejected(competitive_setup):
    event = payload(competitive_setup)
    apply_verified_finalization(event)
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(event, score_a=9))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(event, event_id=uuid.uuid4()))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(event, match_id=uuid.uuid4()))
    assert AppliedMatchEvent.objects.count() == 1


@pytest.mark.django_db
def test_separate_tournament_and_challenge_ratings_and_draw(competitive_setup):
    game, season, _, users = competitive_setup
    event = payload(competitive_setup, kind="challenge", score_a=1, score_b=1)
    apply_verified_finalization(event)
    first = PlayerRating.objects.get(user=users[0], kind="challenge")
    assert (first.rating, first.draws, first.played) == (1000, 1, 1)
    assert not PlayerRating.objects.filter(kind="tournament").exists()
    later = payload(competitive_setup, at=event.finalized_at + timedelta(minutes=1))
    apply_verified_finalization(later)
    assert PlayerRating.objects.get(user=users[0], kind="tournament").rating == 1016
    assert PlayerRating.objects.get(user=users[0], kind="challenge").rating == 1000


@pytest.mark.django_db
def test_validation_unknown_game_invalid_source_and_unconfigured_season(competitive_setup):
    item = payload(competitive_setup)
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(item, game_id="missing"))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(item, score_a=-1))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(item, player_b_id=item.player_a_id))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(item, kind="fake"))
    with pytest.raises(ValidationError):
        apply_verified_finalization(replace(item, finalized_at=timezone.now() + timedelta(days=90)))
    assert PlayerRating.objects.count() == 0


@pytest.mark.django_db
def test_out_of_order_event_fails_closed(competitive_setup):
    newer = payload(competitive_setup, at=timezone.now())
    apply_verified_finalization(newer)
    older = payload(competitive_setup, at=newer.finalized_at - timedelta(hours=1))
    with pytest.raises(ValidationError, match="Out-of-order"):
        apply_verified_finalization(older)
    assert AppliedMatchEvent.objects.count() == 1


@pytest.mark.django_db
def test_public_leaderboard_ordering_and_strict_schema_privacy(competitive_setup):
    game, season, city, users = competitive_setup
    apply_verified_finalization(payload(competitive_setup))
    client = APIClient()
    url = "/api/v1/rankings/?game=ea-fc&season=autumn-2026&type=tournament"
    response = client.get(url)
    assert response.status_code == 200
    body = response.data
    assert body["schemaVersion"] == 1
    assert body["activeQuery"]["game"] == game.slug
    assert [row["rank"] for row in body["items"]] == [1, 2]
    assert [row["rating"] for row in body["items"]] == [1016, 984]
    assert body["pagination"]["totalItems"] == 2
    for key in ("phone", "email", "interview_opt_in", "is_staff", "is_superuser"):
        assert key not in str(body)
    assert client.get(url + "&region=karaj").status_code == 200
    assert client.get(url + "&type=fake").status_code == 400
    assert client.get(url + "&game=not-a-game").status_code == 400
    assert client.get(url + "&page=0").status_code == 400
    assert client.get(url + "&page=999").status_code == 404
    identity = PublicRankingIdentity.objects.get(user=users[0])
    identity.is_published = False
    identity.save(update_fields=["is_published"])
    listed = client.get(url)
    assert listed.data["pagination"]["totalItems"] == 1
    assert listed.data["items"][0]["rank"] == 1


@pytest.mark.django_db
def test_public_profile_requires_publication_and_never_exposes_private_fields(
    competitive_setup,
):
    _, _, _, users = competitive_setup
    apply_verified_finalization(payload(competitive_setup))
    client = APIClient()
    route = "/api/v1/players/gamer_0/public-profile/"
    body = client.get(route)
    assert body.status_code == 200
    assert body.data["username"] == "gamer_0"
    assert body.data["competitiveSnapshots"][0]["rating"] == 1016
    assert len(body.data["recentResults"]) == 1
    assert "phone" not in str(body.data)
    assert "email" not in str(body.data)
    assert client.get("/api/v1/players/no-one/public-profile/").status_code == 404
    user = users[0]
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert client.get(route).status_code == 404


@pytest.mark.django_db
def test_rivalries_are_private_directional_and_never_include_nonfinalized(
    competitive_setup,
):
    _, _, _, users = competitive_setup
    first = payload(competitive_setup)
    apply_verified_finalization(first)
    second = payload(
        competitive_setup, event_id=uuid.uuid4(), match_id=uuid.uuid4(),
        score_a=0, score_b=4, at=first.finalized_at + timedelta(minutes=1),
    )
    apply_verified_finalization(second)
    outsider = users[2]
    anonymous = APIClient().get("/api/v1/me/rivalries/")
    assert anonymous.status_code == 403
    client = APIClient()
    client.force_login(users[0])
    result = client.get("/api/v1/me/rivalries/")
    assert result.status_code == 200
    item = result.data["items"][0]
    assert item["headToHead"] == {
        "totalFinalized": 2, "playerWins": 1, "opponentWins": 1,
        "draws": 0, "edge": "tied",
    }
    assert item["lastEncounter"]["outcome"] == "loss"
    assert result.data["summary"]["totalFinalizedMatches"] == 2
    assert client.get("/api/v1/me/rivalries/?kind=team").data["items"] == []
    assert client.get("/api/v1/me/rivalries/?sort=most-played").status_code == 200
    assert client.get("/api/v1/me/rivalries/?sort=fake").status_code == 400
    client.force_login(outsider)
    assert client.get("/api/v1/me/rivalries/").data["summary"]["totalRivalries"] == 0
    assert "phone" not in str(result.data)


@pytest.mark.django_db
def test_rating_record_database_constraint_prevents_inconsistent_stats(competitive_setup):
    game, season, _, users = competitive_setup
    with pytest.raises(IntegrityError), transaction.atomic():
        PlayerRating.objects.create(
            user=users[0], game=game, season=season,
            kind="tournament", played=3, wins=1,
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_duplicate_delivery_is_one_rating_effect(competitive_setup):
    event = payload(competitive_setup)

    def worker():
        close_old_connections()
        try:
            item, created = apply_verified_finalization(event)
            return item.pk, created
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sum(created for _, created in results) == 1
    assert len({pk for pk, _ in results}) == 1
    assert AppliedMatchEvent.objects.count() == 1
    assert PlayerRating.objects.filter(played=1).count() == 2
