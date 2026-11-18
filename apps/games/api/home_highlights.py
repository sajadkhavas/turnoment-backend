from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.avatars import profile_avatar
from apps.games.selectors import game_identity, published_games
from apps.rankings.models import PublicRankingIdentity
from apps.results.models import FinalizedResultEvent


def results_for_side(side, other):
    return FinalizedResultEvent.objects.filter(
        **{f"player_{side}_id": OuterRef("user_id")}
    ).order_by().values(f"player_{side}_id").annotate(
        played=Count("pk"),
        wins=Count("pk", filter=Q(**{f"score_{side}__gt": F(f"score_{other}")})),
    )


class HomeHighlightsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        side_a, side_b = results_for_side("a", "b"), results_for_side("b", "a")

        def total(field):
            return sum((
                Coalesce(Subquery(side.values(field), output_field=IntegerField()), Value(0))
                for side in (side_a, side_b)
            ), Value(0))

        leaders = PublicRankingIdentity.objects.filter(
            is_published=True, user__is_active=True, user__player_profile__gamer_tag__isnull=False,
        ).exclude(user__player_profile__gamer_tag="").select_related("user__player_profile").annotate(
            played=total("played"), wins=total("wins"),
        ).filter(played__gt=0).order_by("-wins", "username", "pk")[:20]
        return Response({
            "leaders": [{
                "rank": rank,
                "username": identity.username,
                "name": identity.user.player_profile.gamer_tag,
                "avatarUrl": profile_avatar(identity.user.player_profile.avatar_key),
                "wins": identity.wins,
                "level": 1 + identity.wins // 10,
            } for rank, identity in enumerate(leaders, 1)],
            "games": [{
                **game_identity(game), "imageUrl": game.cover_image,
            } for game in published_games().order_by("-is_featured", "sort_order", "id")[:12]],
        })
