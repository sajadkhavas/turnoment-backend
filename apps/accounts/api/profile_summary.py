from django.db.models import Count, F, Max, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils.cache import add_never_cache_headers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.avatars import profile_avatar
from apps.games.models import Game
from apps.gaming_centers.models import GamingCenter
from apps.rankings.models import PlayerRating
from apps.results.models import FinalizedResultEvent
from apps.teams.models import TeamMembership


def player_records(user):
    is_a, is_b = Q(player_a_id=user.pk), Q(player_b_id=user.pk)
    a_wins, b_wins = Q(score_a__gt=F("score_b")), Q(score_b__gt=F("score_a"))
    wins = (is_a & a_wins) | (is_b & b_wins)
    losses = (is_a & b_wins) | (is_b & a_wins)
    rows = list(FinalizedResultEvent.objects.filter(is_a | is_b).order_by().values(
        "match__game_id"
    ).annotate(
        played=Count("pk"),
        wins=Count("pk", filter=wins),
        losses=Count("pk", filter=losses),
        draws=Count("pk", filter=Q(score_a=F("score_b"))),
        gameName=Coalesce(Subquery(Game.objects.filter(
            pk=OuterRef("match__game_id")
        ).values("name")[:1]), Max("match__game_name")),
    ).order_by("-played", "match__game_id"))
    game_ids = [row["match__game_id"] for row in rows]
    ranks = {}
    if game_ids:
        better = (
            Q(rating__gt=OuterRef("rating")) |
            Q(rating=OuterRef("rating"), wins__gt=OuterRef("wins")) |
            Q(rating=OuterRef("rating"), wins=OuterRef("wins"), played__gt=OuterRef("played")) |
            Q(rating=OuterRef("rating"), wins=OuterRef("wins"),
              played=OuterRef("played"), user_id__lt=OuterRef("user_id"))
        )
        ahead = PlayerRating.objects.filter(
            game_id=OuterRef("game_id"), season_id=OuterRef("season_id"), kind=OuterRef("kind"),
            user__is_active=True, user__ranking_identity__is_published=True,
            user__player_profile__gamer_tag__isnull=False,
        ).exclude(user__player_profile__gamer_tag="").filter(better).order_by().values(
            "game_id"
        ).annotate(total=Count("pk")).values("total")
        ratings = PlayerRating.objects.filter(
            user=user, game_id__in=game_ids, played__gt=0,
            game__publication_state=Game.Publication.PUBLISHED, season__is_published=True,
            user__ranking_identity__is_published=True,
            user__player_profile__gamer_tag__isnull=False,
        ).exclude(user__player_profile__gamer_tag="").annotate(
            position=Value(1) + Coalesce(Subquery(ahead), Value(0)),
        ).order_by(
            "-season__starts_at", "-season__slug", "-kind", "pk"
        ).values("game_id", "position", "kind", "season__label")
        for rating in ratings:
            ranks.setdefault(rating["game_id"], {
                "position": rating["position"], "kind": rating["kind"],
                "season": rating["season__label"],
            })
    for row in rows:
        game_id = row.pop("match__game_id")
        row["gameId"] = game_id
        row["rank"] = ranks.get(game_id)
        if not row["gameName"]:
            row["gameName"] = game_id
    return rows


class MyProfileSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "player_profile", None)
        games = player_records(user)
        wins = sum(game["wins"] for game in games)
        memberships = TeamMembership.objects.filter(
            user=user, team__center__isnull=False
        ).select_related("team__center").order_by("-joined_at", "pk")
        response = Response({
            "displayName": (profile.display_name or profile.gamer_tag) if profile else None,
            "gamerTag": profile.gamer_tag if profile else None,
            "avatarUrl": profile_avatar(profile.avatar_key) if profile else None,
            "level": 1 + wins // 10,
            "wins": wins,
            "teams": [{
                "id": str(item.team_id), "name": item.team.name,
                "isPublic": (
                    item.team.center.publication_state == GamingCenter.Publication.PUBLISHED
                ),
            } for item in memberships],
            "games": games,
        })
        add_never_cache_headers(response)
        return response
