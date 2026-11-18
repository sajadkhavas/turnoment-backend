from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matches.models import Match

from .projections import result_view
from .services import confirm_score, submit_score


def private_match(match_id, user):
    match = (
        Match.objects.select_related(
            "participant_a__player_profile", "participant_b__player_profile", "result"
        )
        .filter(pk=match_id)
        .first()
    )
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
            return Response(
                {"outcome": "validation_error", "fields": {"form": "Invalid idempotency key"}},
                status=400,
            )
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("revision"), str):
            return Response(
                {"outcome": "validation_error", "fields": {"form": "Invalid revision"}}, status=400
            )
        return Response(
            submit_score(
                match_id,
                request.user,
                data["revision"],
                data.get("playerScore"),
                data.get("opponentScore"),
                key,
            )
        )


class ConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        private_match(match_id, request.user)
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("revision"), str):
            return Response({"detail": "Invalid request"}, status=400)
        return Response(
            confirm_score(
                match_id,
                request.user,
                data["revision"],
                data.get("playerScore"),
                data.get("opponentScore"),
            )
        )


class VenueResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.matches.projections import tag

        from .venue import result_managers, with_result_venue

        centers = result_managers(request.user).values("center__public_id")
        matches = with_result_venue(Match.objects.filter(
            state__in=(Match.State.AWAITING_RESULT, Match.State.AWAITING_CONFIRMATION)
        )).filter(result_venue_key__in=centers).select_related(
            "participant_a__player_profile", "participant_b__player_profile", "result",
        ).order_by("starts_at", "pk")
        return Response({"items": [{
            "id": str(match.pk),
            "center": match.result_venue_key,
            "title": match.competition_title,
            "playerA": tag(match.participant_a),
            "playerB": tag(match.participant_b),
            "revision": str(match.revision),
            "minScore": match.min_score,
            "maxScore": match.max_score,
            "scoreA": match.result.score_a if hasattr(match, "result") else None,
            "scoreB": match.result.score_b if hasattr(match, "result") else None,
        } for match in matches[:50]], "canManage": centers.exists()})


class VenueResultWriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, center_key, match_id):
        from django.shortcuts import get_object_or_404

        from .services import submit_venue_score
        from .venue import result_managers

        membership = get_object_or_404(
            result_managers(request.user).select_related("center"), center__public_id=center_key,
        )
        key = request.headers.get("Idempotency-Key", "")
        data = request.data
        if not 8 <= len(key) <= 200 or not isinstance(data, dict) or not isinstance(
            data.get("revision"), str
        ):
            return Response({"detail": "Invalid request"}, status=400)
        return Response(submit_venue_score(
            membership.center, match_id, request.user, data["revision"],
            data.get("scoreA"), data.get("scoreB"), key,
        ))
