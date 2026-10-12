"""B02 dashboard: owner-only, truthful unranked state and B08 authoritative data."""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.achievements.models import (
    AchievementCategory,
    AchievementDefinition,
    AchievementProgress,
)
from apps.matches.models import Match
from apps.notifications.models import Notification
from apps.registrations.models import Registration
from apps.results.models import FinalizedResultEvent, MatchResult
from apps.teams.models import Team, TeamMembership
from apps.tournaments.models import Tournament

URL = "/api/v1/me/dashboard/"


def player(phone, tag):
    user = User.objects.create_user(phone=phone)
    PlayerProfile.objects.create(user=user, gamer_tag=tag, display_name=tag, city="کرج")
    return user


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_unranked_owner_has_no_fabricated_public_identity_or_rating():
    user = player("09121234567", "testerA")
    other = player("09121234568", "testerB")
    assert APIClient().get(URL).status_code == 403

    client = client_for(user)
    response = client.get(URL)
    assert response.status_code == 200
    data = response.data
    assert data["identity"]["playerId"] == str(user.pk)
    assert data["identity"]["username"] is None
    assert data["identity"]["gamerTag"] == "testerA"
    assert data["snapshot"] == {
        "tournamentRating": None, "tournamentRank": None,
        "challengeRating": None, "finalizedMatches": 0,
        "tournamentWins": 0, "ratingHistory": [],
    }
    assert data["challengeProgress"] == {
        "finalizedMatches": 0, "requiredMatches": 30, "unlocked": False
    }
    assert data["recentMatches"] == []
    assert data["upcomingMatch"] is None
    assert data["rivalry"] is None
    assert data["team"] is None
    assert data["tournaments"] == []
    assert data["achievements"] == []
    assert data["notifications"] == []
    assert client.get(URL + "?ignored=1").status_code == 400
    assert other.phone not in str(data)
    assert user.phone not in str(data)


@pytest.mark.django_db
def test_real_b08_finalization_populates_records_but_never_invents_elo():
    alice = player("09121234569", "aliceA")
    bob = player("09121234570", "bobB")
    match = Match.objects.create(
        source_kind=Match.Source.TOURNAMENT,
        source_id="tournament-1-match-a", participant_a=alice, participant_b=bob,
        game_id="game-a", game_name="Game A",
        competition_title="Final match", starts_at=timezone.now(),
        state=Match.State.COMPLETED,
    )
    result = MatchResult.objects.create(
        match=match, reported_by=alice, confirmed_by=bob,
        score_a=3, score_b=1, idempotency_key="test-final-1",
        finalized_at=timezone.now(),
    )
    FinalizedResultEvent.objects.create(
        match=match, result=result, score_a=3, score_b=1,
        player_a_id=alice.pk, player_b_id=bob.pk, finalized_at=result.finalized_at,
    )
    alice_data = client_for(alice).get(URL).data
    bob_data = client_for(bob).get(URL).data
    assert alice_data["snapshot"]["finalizedMatches"] == 1
    assert alice_data["snapshot"]["tournamentWins"] == 1
    assert alice_data["snapshot"]["tournamentRating"] is None
    assert alice_data["snapshot"]["tournamentRank"] is None
    assert alice_data["recentMatches"][0]["result"] == "win"
    assert alice_data["recentMatches"][0]["opponentTag"] == "bobB"
    assert alice_data["recentMatches"][0]["ratingDelta"] is None
    assert bob_data["snapshot"]["tournamentWins"] == 0
    assert bob_data["recentMatches"][0]["result"] == "loss"
    assert bob_data["recentMatches"][0]["opponentTag"] == "aliceA"
    assert alice_data["challengeProgress"]["unlocked"] is False


@pytest.mark.django_db
def test_real_registration_team_achievement_and_notification_are_owner_scoped():
    alice = player("09121234571", "aliceX")
    bob = player("09121234572", "bobX")
    tournament = Tournament.objects.create(
        slug="karaj-event", title="Karaj event", description="Test event",
        game_key="game-a", game_slug="game-a", game_name="Game A",
        center_key="center-a", center_name="Venue A", center_city="Karaj",
        center_district="Center", starts_at=timezone.now() + timedelta(days=2),
        display_date="۱۴۰۵/۰۷/۲۲", display_time="۱۸:۰۰", capacity=16,
    )
    Registration.objects.create(user=alice, tournament=tournament)
    team = Team.objects.create(name="Team A", created_by=alice)
    TeamMembership.objects.create(
        team=team, user=alice, role=TeamMembership.Role.CAPTAIN
    )
    TeamMembership.objects.create(team=team, user=bob, role=TeamMembership.Role.MEMBER)
    category = AchievementCategory.objects.create(id="winner", name="Wins")
    definition = AchievementDefinition.objects.create(
        code="first-match", title="First match", description="Play once",
        category=category, is_published=True,
    )
    AchievementProgress.objects.create(
        user=alice, definition=definition, current=1, unlocked_at=timezone.now()
    )
    Notification.objects.create(
        recipient=alice, event_key="real-event-01", kind=Notification.Kind.TOURNAMENT,
        title="Registered", body="Your registration is ready",
        occurred_at=timezone.now(),
    )
    data = client_for(alice).get(URL).data
    assert data["tournaments"][0]["tournamentId"] == str(tournament.pk)
    assert data["nextTournament"]["title"] == "Karaj event"
    assert data["team"]["teamId"] == str(team.pk)
    assert data["team"]["members"] == 2
    assert data["achievements"][0]["unlocked"] is True
    assert data["notifications"][0]["kind"] == "registration"
    other_data = client_for(bob).get(URL).data
    assert other_data["tournaments"] == []
    assert other_data["achievements"][0]["unlocked"] is False
    assert other_data["notifications"] == []
