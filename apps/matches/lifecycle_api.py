from django.db import transaction
from django.db.models import Q
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.challenges.models import Challenge
from apps.matches.models import Match
from apps.matches.services import advance_match


@transaction.atomic
def change_challenge_match(match_id, user, command, revision):
    match = (
        Match.objects.select_for_update()
        .filter(Q(participant_a=user) | Q(participant_b=user), pk=match_id)
        .first()
    )
    if match is None:
        raise Http404
    if match.source_kind != Match.Source.CHALLENGE:
        return {"outcome": "unavailable"}
    challenge = Challenge.objects.filter(
        match_id=str(match.pk),
        state=Challenge.State.ACCEPTED,
        challenger_id=match.participant_a_id,
        opponent_id=match.participant_b_id,
    ).first()
    if (
        challenge is None
        or str(challenge.pk) != match.source_id
        or challenge.game_id != match.game_id
    ):
        return {"outcome": "unavailable"}
    if revision != str(match.revision):
        return {"outcome": "stale", "revision": str(match.revision)}
    transitions = {
        "start": (Match.State.READY, Match.State.LIVE),
        "finish": (Match.State.LIVE, Match.State.AWAITING_RESULT),
    }
    expected, target = transitions[command]
    if match.state != expected:
        return {"outcome": "unavailable"}
    match = advance_match(match.pk, target)
    return {
        "outcome": "accepted",
        "matchId": str(match.pk),
        "state": match.state,
        "revision": str(match.revision),
    }


class ChallengeMatchLifecycleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        data = request.data
        if (
            not isinstance(data, dict)
            or data.get("command") not in ("start", "finish")
            or not isinstance(data.get("revision"), str)
            or not data["revision"]
            or len(data["revision"]) > 20
        ):
            return Response({"detail": "Invalid lifecycle command"}, status=400)
        return Response(change_challenge_match(
            match_id, request.user, data["command"], data["revision"],
        ))
