from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.identifiers import uuid_public_id

from ..models import TeamInvite
from ..projections import team_page
from ..services import create_team, invite, leave, respond, transfer_captain


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
        data = TeamCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        team = create_team(user=request.user, name=data.validated_data["name"])
        return Response({"teamId": uuid_public_id(team.pk), "name": team.name}, status=201)


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
