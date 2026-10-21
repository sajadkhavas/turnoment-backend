from apps.matches.models import Match
from apps.matches.projections import common


def reported_score(match, result, user):
    if not result:
        return None
    a, b = (
        (result.score_a, result.score_b)
        if match.participant_a_id == user.pk
        else (result.score_b, result.score_a)
    )
    return {"playerScore": a, "opponentScore": b, "reportedAt": result.reported_at.isoformat()}


def final_result(match, result, user):
    if not result or not result.finalized_at:
        return None
    a, b = (
        (result.score_a, result.score_b)
        if match.participant_a_id == user.pk
        else (result.score_b, result.score_a)
    )
    from apps.rankings.models import AppliedMatchEvent

    applied = AppliedMatchEvent.objects.filter(source_match_id=match.pk).first()
    delta = None
    if applied:
        delta = (
            applied.rating_a_after - applied.rating_a_before
            if applied.user_a_id == user.pk
            else applied.rating_b_after - applied.rating_b_before
        )
    return {
        "playerScore": a,
        "opponentScore": b,
        "outcome": "draw" if a == b else "win" if a > b else "loss",
        "ratingDelta": delta,
        "finalizedAt": result.finalized_at.isoformat(),
    }


def result_view(match, user):
    result = getattr(match, "result", None)
    state = {
        Match.State.AWAITING_RESULT: "reportable",
        Match.State.AWAITING_CONFIRMATION: "awaiting-confirmation",
        Match.State.COMPLETED: "finalized",
        Match.State.DISPUTED: "disputed",
    }.get(match.state, "unavailable")
    data = common(match, user)
    data.update(
        {
            "revision": str(match.revision),
            "submissionState": state,
            "canConfirmResult": bool(
                state == "awaiting-confirmation" and result and result.reported_by_id != user.pk
            ),
            "scorePolicy": {
                "minScore": match.min_score,
                "maxScore": match.max_score,
                "allowDraw": match.allow_draw,
            },
            "reportedScore": reported_score(match, result, user),
            "finalResult": final_result(match, result, user),
        }
    )
    return data


def receipt(match, result, user, replay=False):
    status = "finalized" if result.finalized_at else "awaiting-confirmation"
    payload = {
        "status": status,
        "reportedScore": reported_score(match, result, user),
        "finalResult": final_result(match, result, user),
    }
    if replay:
        return {"outcome": "already_submitted", **payload}
    return {"outcome": "accepted", "receiptId": str(result.pk), "matchId": str(match.pk), **payload}
