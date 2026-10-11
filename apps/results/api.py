from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matches.models import Match

from .projections import result_view
from .services import confirm_score, submit_score


def private_match(match_id, user):
    match = Match.objects.select_related(
        "participant_a__player_profile", "participant_b__player_profile", "result"
    ).filter(pk=match_id).first()
    if match is None or not match.has_participant(user):
        raise Http404
    return match


class ResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        return Response(result_view(private_match(match_id, request.user), request.user))

    def post(self, request, match_id):
        private_match(match_id, request.user)
        key = request.headers.get("Idempotency-Key", "")
        if not 8 <= len(key) <= 200:
            return Response({"outcome": "validation_error", "fields": {"form": "Invalid idempotency key"}}, status=400)
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("revision"), str):
            return Response({"outcome": "validation_error", "fields": {"form": "Invalid revision"}}, status=400)
        return Response(submit_score(match_id, request.user, data["revision"], data.get("playerScore"), data.get("opponentScore"), key))


class ConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        private_match(match_id, request.user)
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("revision"), str):
            return Response({"detail": "Invalid request"}, status=400)
        return Response(confirm_score(match_id, request.user, data["revision"], data.get("playerScore"), data.get("opponentScore")))
