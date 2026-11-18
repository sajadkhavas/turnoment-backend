from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.games.models import Game
from apps.gaming_centers.models import City, GamingCenter
from apps.matches.models import Match
from apps.rankings.models import PlayerRating, PublicRankingIdentity, Season
from apps.results.models import FinalizedResultEvent, MatchResult
from apps.teams.models import Team, TeamMembership

URL = "/api/v1/me/profile-summary/"


@pytest.mark.django_db
def test_profile_summary_uses_final_results_and_keeps_private_data_scoped():
    me, opponent, outsider = [
        User.objects.create_user(phone=f"0912300000{number}") for number in range(1, 4)
    ]
    PlayerProfile.objects.create(
        user=me, gamer_tag="OwnHandle", display_name="My Name", bio="Private note",
        avatar_key="/api/v1/media/photos/11111111-1111-1111-1111-111111111111/image/",
    )
    PlayerProfile.objects.create(user=opponent, gamer_tag="Opponent")
    now = timezone.now()
    game = Game.objects.create(
        slug="active-game", name="Active game", short_name="Active",
        description="Competitive gaming test fixture", platforms=["PC"],
        publication_state=Game.Publication.PUBLISHED
    )
    unused = Game.objects.create(
        slug="unused-game", name="Unused game", short_name="Unused",
        description="Competitive gaming test fixture", platforms=["PC"],
        publication_state=Game.Publication.PUBLISHED
    )
    city = City.objects.create(name="کرج", slug="karaj")
    center = GamingCenter.objects.create(name="Center", city=city, public_id="c1")
    team = Team.objects.create(center=center, name="Private Team", created_by=opponent)
    TeamMembership.objects.create(team=team, user=me)
    current = Season.objects.create(
        slug="current", label="Current", is_published=True,
        starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=1),
    )
    for user, rating in [(me, 1000), (opponent, 1100), (outsider, 1200)]:
        PlayerRating.objects.create(
            user=user, game=game, season=current, kind="tournament",
            rating=rating, played=1, wins=1,
        )
    for user, username in [(me, "own-handle"), (opponent, "opponent")]:
        PublicRankingIdentity.objects.create(
            user=user, username=username, city=city, is_published=True
        )

    for index, (a, b, score_a, score_b) in enumerate([
        (me, opponent, 3, 1), (opponent, me, 1, 2),
        (opponent, me, 3, 1), (me, opponent, 2, 2),
    ]):
        match = Match.objects.create(
            source_kind="tournament", source_id=f"profile-match-{index}",
            participant_a=a, participant_b=b, game_id=game.pk, starts_at=now,
            state=Match.State.COMPLETED,
        )
        result = MatchResult.objects.create(
            match=match, reported_by=a, confirmed_by=b, idempotency_key=f"result-{index}",
            score_a=score_a, score_b=score_b, finalized_at=now,
        )
        FinalizedResultEvent.objects.create(
            match=match, result=result, score_a=score_a, score_b=score_b,
            player_a_id=a.pk, player_b_id=b.pk, finalized_at=now,
        )
    Match.objects.create(
        source_kind="tournament", source_id="upcoming", participant_a=me,
        participant_b=opponent, game_id=unused.pk, starts_at=now,
    )

    api = APIClient()
    assert api.get(URL).status_code in (401, 403)
    api.force_authenticate(me)
    summary = api.get(URL)
    assert summary.status_code == 200
    assert "no-store" in summary["Cache-Control"]
    assert summary.data["avatarUrl"] == me.player_profile.avatar_key
    assert summary.data["wins"] == 2
    assert summary.data["level"] == 1
    assert summary.data["teams"] == [{"id": str(team.pk), "name": team.name, "isPublic": False}]
    assert summary.data["games"] == [{
        "gameId": game.pk, "gameName": game.name, "played": 4, "wins": 2,
        "losses": 1, "draws": 1,
        "rank": {"position": 2, "kind": "tournament", "season": "Current"},
    }]
    assert "Private note" not in str(summary.data)
    assert me.phone not in str(summary.data)
    PublicRankingIdentity.objects.filter(user=me).update(is_published=False)
    assert api.get(URL).data["games"][0]["rank"] is None
    api.force_authenticate(outsider)
    assert api.get(URL).data["games"] == []
    assert api.get(URL).data["teams"] == []
