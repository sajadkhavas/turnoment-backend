from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PlayerProfile


class CurrentPlayerIdentityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        tag = profile.gamer_tag or ""
        return Response({
            "playerId": str(request.user.pk),
            "username": tag,
            "gamerTag": tag,
            "displayName": profile.display_name,
            "city": profile.city,
        })
