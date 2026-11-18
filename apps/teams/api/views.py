from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PlayerProfile
from apps.gaming_centers.models import CenterMembership

from ..models import Team, TeamInvite
from ..projections import team_page
from ..services import create_center_team, invite, leave, respond, transfer_captain


class StrictInput(serializers.Serializer):
    def validate(self, attrs):
        if set(self.initial_data) != set(self.fields):
            raise serializers.ValidationError("Exactly the specified fields are required.")
        return attrs


class TeamCreateInput(StrictInput):
    name = serializers.CharField(min_length=1, max_length=120, trim_whitespace=True)


class TeamInviteInput(StrictInput):
    playerId = serializers.UUIDField()


class CaptainInput(StrictInput):
    playerId = serializers.UUIDField()


class MyTeamsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(team_page(request.user, request.query_params))


class TeamCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raise PermissionDenied("Teams can only be created by a gaming center.")


class ManagedCentersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = CenterMembership.objects.filter(
            user=request.user, is_active=True,
            role__in=(CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER),
        ).select_related("center", "center__competitive_team").order_by("center__name", "center_id")
        return Response({"items": [
            {"id": str(m.center_id), "name": m.center.name,
             "team": CenterTeamView.summary(team) if (team := getattr(
                 m.center, "competitive_team", None
             )) else None}
            for m in memberships
        ]})


class CenterInviteInput(StrictInput):
    gamerTag = serializers.CharField(max_length=24)


class CenterTeamInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        if not Team.objects.filter(
            pk=team_id, center__memberships__user=request.user,
            center__memberships__is_active=True,
            center__memberships__role__in=(
                CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER,
            ),
        ).exists():
            raise PermissionDenied("Active center owner or manager permission required.")
        data = CenterInviteInput(data=request.data)
        data.is_valid(raise_exception=True)
        profile = PlayerProfile.objects.filter(
            gamer_tag__iexact=data.validated_data["gamerTag"], user__is_active=True
        ).first()
        if profile is None:
            return Response({"detail": "Player not found."}, status=404)
        obj, created = invite(actor=request.user, team_id=team_id, recipient_id=profile.user_id)
        return Response({"inviteId": str(obj.pk)}, status=201 if created else 200)


class TeamImageInput(StrictInput):
    image = serializers.URLField(max_length=2048, allow_blank=True)

    def validate_image(self, value):
        from urllib.parse import urlsplit

        if value:
            url = urlsplit(value)
            if url.scheme != "https" or url.username or url.password:
                raise serializers.ValidationError("Use a public HTTPS image URL.")
        return value


class CenterTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, center_id):
        if not CenterMembership.objects.filter(
            center_id=center_id,
            user=request.user,
            is_active=True,
            role__in=(CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER),
        ).exists():
            raise PermissionDenied("Active center owner or manager permission required.")
        team = Team.objects.filter(center_id=center_id).first()
        return Response({"team": None if team is None else self.summary(team)})

    def post(self, request, center_id):
        data = TeamCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        team = create_center_team(
            actor=request.user, center_id=center_id, name=data.validated_data["name"]
        )
        return Response({"team": self.summary(team)}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request, center_id):
        managed = CenterMembership.objects.select_for_update().filter(
            center_id=center_id, user=request.user, is_active=True,
            role__in=(CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER),
        ).first()
        if managed is None:
            raise PermissionDenied("Active center owner or manager permission required.")
        data = TeamImageInput(data=request.data)
        data.is_valid(raise_exception=True)
        team = get_object_or_404(Team.objects.select_for_update(), center_id=center_id)
        team.image_url = data.validated_data["image"]
        team.save(update_fields=["image_url"])
        return Response({"team": self.summary(team)})

    @staticmethod
    def summary(team):
        return {"teamId": str(team.pk), "name": team.name, "image": team.image_url}


class TeamInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        data = TeamInviteInput(data=request.data)
        data.is_valid(raise_exception=True)
        obj, created = invite(
            actor=request.user, team_id=team_id, recipient_id=data.validated_data["playerId"]
        )
        return Response(
            {"inviteId": str(obj.pk), "state": obj.state},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MyTeamInvitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.query_params:
            raise serializers.ValidationError({"query": ["Unexpected filter."]})
        invites = TeamInvite.objects.filter(
            recipient=request.user, state=TeamInvite.State.PENDING
        ).select_related("team").order_by("created_at", "id")[:100]
        return Response({"items": [
            {"inviteId": str(item.pk), "teamId": str(item.team_id), "teamName": item.team.name}
            for item in invites
        ]})


class InvitationActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id, action):
        if action not in ("accept", "decline"):
            return Response({"detail": "Unknown action."}, status=404)
        if request.data:
            raise serializers.ValidationError({"detail": ["This command takes no fields."]})
        obj = respond(actor=request.user, invite_id=invite_id, accept=action == "accept")
        return Response({"inviteId": str(obj.pk), "state": obj.state})


class CaptainTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        data = CaptainInput(data=request.data)
        data.is_valid(raise_exception=True)
        obj = transfer_captain(
            actor=request.user, team_id=team_id, new_captain_id=data.validated_data["playerId"]
        )
        return Response({"teamId": str(obj.team_id), "captainId": str(obj.user_id)})


class TeamLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        if request.data:
            raise serializers.ValidationError({"detail": ["This command takes no fields."]})
        leave(actor=request.user, team_id=team_id)
        return Response(status=204)
