from math import ceil

from django.db.models import Count, Exists, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gaming_centers.models import GamingCenter
from apps.rankings.models import PublicRankingIdentity
from apps.results.models import FinalizedResultEvent
from apps.teams.models import Team, TeamMembership

PAGE_SIZE = 20


def public_teams():
    winning_member = TeamMembership.objects.filter(
        team_id=OuterRef(OuterRef("pk")), joined_at__lte=OuterRef("finalized_at")
    ).filter(
        Q(user_id=OuterRef("player_a_id"))
    )
    winning_member_b = TeamMembership.objects.filter(
        team_id=OuterRef(OuterRef("pk")), joined_at__lte=OuterRef("finalized_at"),
        user_id=OuterRef("player_b_id"),
    )
    wins = FinalizedResultEvent.objects.alias(
        member_a=Exists(winning_member), member_b=Exists(winning_member_b)
    ).filter(
        Q(member_a=True, score_a__gt=F("score_b")) |
        Q(member_b=True, score_b__gt=F("score_a"))
    ).order_by().annotate(group=Value(1)).values("group").annotate(
        count=Count("pk")
    ).values("count")
    return Team.objects.filter(
        center__publication_state=GamingCenter.Publication.PUBLISHED
    ).select_related("center").annotate(
        wins=Coalesce(Subquery(wins, output_field=IntegerField()), Value(0)),
    )


def team_card(team):
    return {
        "id": str(team.pk),
        "name": team.name,
        "image": team.image_url or team.center.cover_image or None,
        "center": {"id": team.center.public_id, "name": team.center.name},
        "wins": team.wins,
        "level": 1 + team.wins // 10,
    }


def get_page(request):
    raw = request.query_params.get("page", "1")
    if not raw.isascii() or not raw.isdecimal() or len(raw) > 6 or int(raw) < 1:
        raise ValidationError({"page": "Invalid page."})
    return int(raw)


class PublicTeamList(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) > 120:
            raise ValidationError({"q": "Search is too long."})
        page = get_page(request)
        teams = public_teams().filter(name__icontains=query).order_by("-wins", "name", "pk")
        center = request.query_params.get("center")
        if center is not None:
            teams = teams.filter(center__public_id=center)
        pages = max(1, ceil(teams.count() / PAGE_SIZE))
        page = min(page, pages)
        return Response({
            "items": [team_card(team) for team in teams[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]],
            "page": page,
            "pages": pages,
        })


class PublicTeamDetail(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, team_id):
        team = get_object_or_404(public_teams(), pk=team_id)
        members = PublicRankingIdentity.objects.filter(
            user__team_memberships__team=team,
            is_published=True, user__is_active=True,
        ).exclude(user__player_profile__gamer_tag__isnull=True).exclude(
            user__player_profile__gamer_tag=""
        ).select_related("user__player_profile").order_by("username", "pk")
        pages = max(1, ceil(members.count() / PAGE_SIZE))
        page = min(get_page(request), pages)
        return Response({
            **team_card(team),
            "memberCount": team.memberships.filter(user__is_active=True).count(),
            "members": [
                {"username": identity.username, "gamerTag": identity.user.player_profile.gamer_tag}
                for identity in members[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
            ],
            "page": page,
            "pages": pages,
        })
