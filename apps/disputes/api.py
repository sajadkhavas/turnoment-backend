from django.http import Http404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matches.models import Match

from .projections import dispute_view
from .services import add_evidence, create_dispute


def private_match(match_id, user):
    match = (
        Match.objects.select_related(
            "participant_a__player_profile", "participant_b__player_profile", "result", "dispute"
        )
        .filter(pk=match_id)
        .first()
    )
    if match is None or not match.has_participant(user):
        raise Http404
    return match


class DisputeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, match_id):
        return Response(dispute_view(private_match(match_id, request.user), request.user))

    def post(self, request, match_id):
        private_match(match_id, request.user)
        body = request.data
        key = request.headers.get("Idempotency-Key", "")
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("revision"), str)
            or not 8 <= len(key) <= 200
        ):
            return Response(
                {"outcome": "validation_error", "fields": {"form": "Invalid command"}}, status=400
            )
        return Response(
            create_dispute(
                match_id,
                request.user,
                body["revision"],
                body.get("reason"),
                body.get("statement"),
                key,
            )
        )


class EvidenceView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, match_id, dispute_id):
        private_match(match_id, request.user)
        key = request.headers.get("Idempotency-Key", "")
        revision = request.data.get("revision")
        if not isinstance(revision, str) or not 8 <= len(key) <= 200:
            return Response({"outcome": "validation_error", "form": "Invalid command"}, status=400)
        return Response(
            add_evidence(
                match_id, dispute_id, request.user, revision, key, request.FILES.get("file")
            )
        )
