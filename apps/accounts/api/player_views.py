import re

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PlayerProfile

_USERNAME = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


class PublicPlayerProfileView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, gamer_tag):
        if not _USERNAME.fullmatch(gamer_tag):
            return Response(
                {"error": {"code": "player_not_found", "message": "Player not found."}},
                status=404,
            )
        profile = PlayerProfile.objects.filter(
            gamer_tag__iexact=gamer_tag, user__is_active=True
        ).first()
        if profile is None:
            return Response(
                {"error": {"code": "player_not_found", "message": "Player not found."}},
                status=404,
            )
        # B09/B08 alone own competitive snapshots and finalized match results.
        # Never synthesize rankings, timestamps, or results here.
        return Response({
            "schemaVersion": 1,
            "publicationState": "published",
            "searchVisibility": "noindex",
            "playerId": str(profile.user_id),
            "username": gamer_tag,
            "gamerTag": profile.gamer_tag,
            "avatarUrl": None,
            "city": None,
            "publicBio": profile.bio.strip() or None,
            "competitiveSnapshots": [],
            "recentResults": [],
        })
