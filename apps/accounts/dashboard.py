"""B02 owner-only dashboard assembled from durable B03–B10 domain records.

Absent rating / published ranking identity is represented by null; never fabricate
a rank, username, match, achievement, or scheduled event.
"""
from zoneinfo import ZoneInfo

from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.timesince import timesince
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.achievements.models import AchievementDefinition, AchievementProgress
from apps.challenges.integrations import player_challenge_stats
from apps.challenges.models import Challenge
from apps.matches.models import Match
from apps.matches.projections import visible_matches
from apps.notifications.models import Notification
from apps.rankings.api import public_ratings
from apps.rankings.models import AppliedMatchEvent, PlayerRating, PublicRankingIdentity
from apps.registrations.models import Registration
from apps.teams.models import TeamMembership

TEHRAN = ZoneInfo("Asia/Tehran")


def label(user):
    profile = getattr(user, "player_profile", None)
    return (profile.gamer_tag if profile and profile.gamer_tag else None) or (
        "player-" + user.pk.hex[:12]
    )


def published_username(user):
    return PublicRankingIdentity.objects.filter(
        user=user, is_published=True,
        user__is_active=True, user__player_profile__gamer_tag__isnull=False,
    ).exclude(
        user__player_profile__gamer_tag=""
    ).values_list("username", flat=True).first()


def iso_date(value):
    return value.astimezone(TEHRAN).strftime("%Y-%m-%d")


def competition_scope(user):
    return PlayerRating.objects.filter(
        user=user, kind=PlayerRating.Kind.TOURNAMENT,
        played__gt=0, season__is_published=True,
        game__publication_state="published",
    ).select_related("game", "season").order_by(
        "-last_finalized_at", "game__slug", "season__slug"
    ).first()


def rank_for(scope, user):
    if scope is None or published_username(user) is None:
        return None
    ranking = public_ratings(scope.game, scope.season, scope.kind)
    if not ranking.filter(user=user).exists():
        return None
    before = ranking.filter(
        Q(rating__gt=scope.rating)
        | Q(rating=scope.rating, wins__gt=scope.wins)
        | Q(rating=scope.rating, wins=scope.wins, played__gt=scope.played)
        | Q(
            rating=scope.rating, wins=scope.wins,
            played=scope.played, user_id__lt=user.pk,
        )
    ).count()
    return before + 1


def ratings(user, scope):
    candidates = PlayerRating.objects.filter(
        user=user, kind=PlayerRating.Kind.CHALLENGE, played__gt=0,
        season__is_published=True, game__publication_state="published",
    ).select_related("game")
    if scope is not None:
        candidates = candidates.filter(game=scope.game, season=scope.season)
    challenge = candidates.order_by("-last_finalized_at", "game__slug").first()
    challenge_rating = challenge.rating if challenge else None
    if scope is None:
        history = []
    else:
        events = list(AppliedMatchEvent.objects.filter(
            Q(user_a=user) | Q(user_b=user),
            game=scope.game, season=scope.season, kind="tournament",
        ).order_by("-finalized_at", "-id")[:10])
        history = [
            event.rating_a_after if event.user_a_id == user.pk else event.rating_b_after
            for event in reversed(events)
        ]
    return scope.rating if scope else None, rank_for(scope, user), challenge_rating, history, challenge


def tournament_state(tournament):
    if tournament.lifecycle == tournament.Lifecycle.COMPLETED:
        return "completed"
    if tournament.lifecycle == tournament.Lifecycle.LIVE:
        return "live"
    return "upcoming"


def tournament_item(reg):
    t = reg.tournament
    state = tournament_state(t)
    return {
        "tournamentId": str(t.pk), "tournamentSlug": t.slug, "title": t.title,
        "gameId": t.game_key, "game": t.game_name,
        "gamingCenterId": t.center_key, "venue": t.center_name,
        "date": t.display_date, "time": t.display_time,
        "format": t.format_label, "registrationState": "ثبت‌نام تأیید شده",
        "tournamentState": state,
        "nextActionLabel": "مشاهده نتایج" if state == "completed"
        else "مشاهده جدول" if state == "live" else "مشاهده تورنمنت",
    }


def match_item(match, user, receipt):
    is_a = match.participant_a_id == user.pk
    other = match.participant_b if is_a else match.participant_a
    result = match.result
    own, peer = (
        (result.score_a, result.score_b) if is_a
        else (result.score_b, result.score_a)
    )
    rating_delta = None
    if receipt:
        before = receipt.rating_a_before if is_a else receipt.rating_b_before
        after = receipt.rating_a_after if is_a else receipt.rating_b_after
        rating_delta = after - before
    return {
        "matchId": str(match.pk), "opponentUsername": published_username(other) or "",
        "opponentTag": label(other), "gameId": match.game_id,
        "game": match.game_name, "competition": match.competition_title,
        "kind": match.source_kind, "score": f"{own} - {peer}",
        "result": "win" if own > peer else "loss" if own < peer else "draw",
        "date": iso_date(result.finalized_at), "ratingDelta": rating_delta,
    }


def upcoming_item(match, user):
    other = match.participant_b if match.participant_a_id == user.pk else match.participant_a
    return {
        "matchId": str(match.pk),
        "tournamentId": match.source_id, "tournamentSlug": match.tournament_slug,
        "competition": match.competition_title, "round": match.round_label,
        "gameId": match.game_id, "game": match.game_name,
        "opponentUsername": published_username(other) or "",
        "opponentTag": label(other),
        "time": match.starts_at.astimezone(TEHRAN).strftime("%H:%M"),
        "venue": match.venue_name, "statusLabel": match.get_state_display(),
    }


def challenge_item(challenge, user):
    incoming = challenge.opponent_id == user.pk
    other = challenge.challenger if incoming else challenge.opponent
    return {
        "challengeId": str(challenge.pk),
        "opponentUsername": published_username(other) or "",
        "opponentTag": label(other), "gameId": challenge.game_id,
        "game": challenge.game_name,
        "direction": "incoming" if incoming else "outgoing",
        "statusLabel": challenge.get_state_display(),
        "isNew": incoming and challenge.state == Challenge.State.PENDING,
    }


def rivalry_preview(user):
    events = AppliedMatchEvent.objects.filter(Q(user_a=user) | Q(user_b=user))
    last = events.order_by("-finalized_at", "-id").first()
    if last is None:
        return None
    rival_id = last.user_b_id if last.user_a_id == user.pk else last.user_a_id
    from apps.accounts.models import User

    rival = User.objects.select_related("player_profile").get(pk=rival_id)
    pair = events.filter(
        Q(user_a=user, user_b=rival) | Q(user_a=rival, user_b=user)
    )
    record = pair.aggregate(
        meetings=Count("id"),
        wins=Count("id", filter=(
            Q(user_a=user, score_a__gt=F("score_b"))
            | Q(user_b=user, score_b__gt=F("score_a"))
        )),
        losses=Count("id", filter=(
            Q(user_a=user, score_a__lt=F("score_b"))
            | Q(user_b=user, score_b__lt=F("score_a"))
        )),
    )
    return {
        "rivalryId": str(rival_id),
        "opponentUsername": published_username(rival) or "",
        "opponentTag": label(rival),
        "playerScore": record["wins"], "opponentScore": record["losses"],
        "meetings": record["meetings"], "lastMeeting": iso_date(last.finalized_at),
    }


def team_preview(user):
    membership = TeamMembership.objects.filter(user=user).select_related("team").annotate(
        member_count=Count("team__memberships")
    ).order_by("joined_at", "id").first()
    if membership is None:
        return None
    team_registration = Registration.objects.filter(
        team_id=str(membership.team_id), status=Registration.Status.CONFIRMED
    ).select_related("tournament").order_by("tournament__starts_at").first()
    game = team_registration.tournament if team_registration else None
    return {
        "teamId": str(membership.team_id), "name": membership.team.name,
        "members": membership.member_count,
        "gameId": game.game_key if game else "", "game": game.game_name if game else "",
        "upcomingEvents": Registration.objects.filter(
            team_id=str(membership.team_id), status=Registration.Status.CONFIRMED,
            tournament__starts_at__gte=timezone.now(),
        ).count(),
    }


def achievement_preview(user):
    definitions = AchievementDefinition.objects.filter(is_published=True).order_by(
        "position", "code"
    )[:4]
    progress = {
        obj.definition_id: obj for obj in AchievementProgress.objects.filter(
            user=user, definition__in=definitions
        )
    }
    return [{
        "achievementId": str(definition.pk), "title": definition.title,
        "description": definition.description,
        "unlocked": bool(progress.get(definition.pk) and progress[definition.pk].unlocked_at),
    } for definition in definitions]


def notification_preview(user):
    # F01 dashboard preview only has four kinds. Account/system remain on full inbox.
    kinds = {
        Notification.Kind.TOURNAMENT: "registration",
        Notification.Kind.MATCH: "result",
        Notification.Kind.CHALLENGE: "challenge",
    }
    latest = Notification.objects.filter(
        recipient=user, kind__in=kinds
    ).order_by("-occurred_at", "-id")[:4]
    return [{
        "notificationId": str(item.pk), "kind": kinds[item.kind],
        "title": item.title, "timeAgo": timesince(item.occurred_at),
        "unread": item.read_at is None, "href": "/dashboard/notifications",
    } for item in latest]


def next_action(tournament, upcoming, confirmation):
    if confirmation is not None:
        return {
            "kind": "result-confirmation", "title": "نتیجه منتظر تأیید شماست",
            "description": confirmation.competition_title,
            "ctaLabel": "بررسی نتیجه", "ctaHref": "/dashboard/matches",
            "meta": [confirmation.game_name], "tone": "warning",
        }
    if upcoming is not None:
        return {
            "kind": "match-ready", "title": "مسابقه آینده شما",
            "description": upcoming.competition_title,
            "ctaLabel": "مشاهده مسابقات", "ctaHref": "/dashboard/matches",
            "meta": [upcoming.game_name], "tone": "primary",
        }
    if tournament is not None:
        return {
            "kind": "tournament-approaching", "title": "تورنمنت ثبت‌نام‌شده",
            "description": tournament["title"],
            "ctaLabel": "مشاهده تورنمنت", "ctaHref": "/tournaments",
            "meta": [tournament["game"]], "tone": "primary",
        }
    return {
        "kind": "none", "title": "اقدام ضروری ندارید",
        "description": "مسابقه یا دعوت جدید را از داشبورد دنبال کنید.",
        "ctaLabel": "", "ctaHref": "/dashboard", "meta": [], "tone": "muted",
    }


def build_dashboard(user):
    """Owner-only bounded reads. No fake public handle or rating for new accounts."""
    profile = getattr(user, "player_profile", None)
    name = label(user)
    scope = competition_scope(user)
    tournament_rating, tournament_rank, challenge_rating, history, challenge_scope = (
        ratings(user, scope)
    )
    registration_rows = list(
        Registration.objects.filter(
            user=user, status=Registration.Status.CONFIRMED
        ).exclude(tournament__lifecycle="cancelled").select_related(
            "tournament"
        ).order_by("-tournament__starts_at", "id")[:5]
    )
    tournaments = [tournament_item(reg) for reg in registration_rows]
    upcoming_registration = Registration.objects.filter(
        user=user, status=Registration.Status.CONFIRMED,
        tournament__starts_at__gte=timezone.now(),
    ).exclude(
        tournament__lifecycle__in=["cancelled", "completed"]
    ).select_related("tournament").order_by("tournament__starts_at", "id").first()
    next_tournament = (
        tournament_item(upcoming_registration) if upcoming_registration else None
    )
    match_qs = visible_matches(user)
    recents = list(match_qs.filter(
        state=Match.State.COMPLETED, result__finalized_at__isnull=False
    ).order_by("-result__finalized_at", "-id")[:5])
    receipts = {
        item.source_match_id: item for item in AppliedMatchEvent.objects.filter(
            source_match_id__in=[m.pk for m in recents]
        )
    }
    future = match_qs.filter(
        source_kind=Match.Source.TOURNAMENT,
        starts_at__gte=timezone.now()
    ).exclude(
        state__in=[Match.State.COMPLETED, Match.State.CANCELLED]
    ).order_by("starts_at", "id").first()
    confirmation = match_qs.filter(
        state=Match.State.AWAITING_CONFIRMATION,
    ).exclude(result__reported_by=user).order_by("-starts_at").first()
    challenge_rows = Challenge.objects.filter(
        Q(challenger=user) | Q(opponent=user)
    ).select_related(
        "challenger__player_profile", "opponent__player_profile"
    ).order_by("-created_at", "-id")[:5]
    stats = player_challenge_stats(user)
    finalized_tournaments = match_qs.filter(
        state=Match.State.COMPLETED, source_kind=Match.Source.TOURNAMENT,
        result__finalized_at__isnull=False
    )
    wins = (
        finalized_tournaments.filter(participant_a=user, result__score_a__gt=F("result__score_b"))
        | finalized_tournaments.filter(participant_b=user, result__score_b__gt=F("result__score_a"))
    ).distinct().count()
    primary_game_id = (
        scope.game_id if scope else challenge_scope.game_id if challenge_scope else
        registration_rows[0].tournament.game_key if registration_rows else ""
    )
    primary_game_name = (
        scope.game.name if scope else challenge_scope.game.name if challenge_scope else
        registration_rows[0].tournament.game_name if registration_rows else ""
    )
    return {
        "identity": {
            "playerId": str(user.pk), "username": published_username(user),
            "gamerTag": name, "displayName": (
                profile.display_name if profile and profile.display_name else name
            ), "city": profile.city if profile else "",
            "primaryGameId": primary_game_id, "primaryGame": primary_game_name,
            "statusLabel": "بازیکن فعال" if user.is_active else "غیرفعال",
            "avatarInitials": name[:2].upper(),
        },
        "snapshot": {
            "tournamentRating": tournament_rating, "tournamentRank": tournament_rank,
            "challengeRating": challenge_rating,
            "finalizedMatches": stats.finalized_valid_matches,
            "tournamentWins": wins, "ratingHistory": history,
        },
        "challengeProgress": {
            "finalizedMatches": stats.finalized_valid_matches,
            "requiredMatches": 30,
            "unlocked": stats.finalized_valid_matches >= 30,
        },
        "nextAction": next_action(next_tournament, future, confirmation),
        "nextTournament": next_tournament,
        "upcomingMatch": upcoming_item(future, user) if future else None,
        "recentMatches": [match_item(m, user, receipts.get(m.pk)) for m in recents],
        "tournaments": tournaments, "challenges": [
            challenge_item(item, user) for item in challenge_rows
        ],
        "rivalry": rivalry_preview(user),
        "team": team_preview(user),
        "achievements": achievement_preview(user),
        "notifications": notification_preview(user),
    }


class MyDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.query_params:
            return Response({"error": {"code": "unexpected_dashboard_query"}}, status=400)
        return Response(build_dashboard(request.user))
