from apps.matches.models import Match
from apps.matches.projections import common
from apps.results.projections import final_result

REASONS = [
    "incorrect-score", "rule-violation", "no-show",
    "technical-issue", "unsportsmanlike-conduct", "other",
]
MAX_FILES = 3
MAX_BYTES = 5 * 1024 * 1024


def evidence_data(e):
    return {
        "evidenceId": str(e.pk), "fileName": e.file_name,
        "contentType": e.content_type, "sizeBytes": e.size_bytes,
        "uploadedAt": e.uploaded_at.isoformat(),
    }


def dispute_data(dispute):
    return {
        "disputeId": str(dispute.pk), "status": dispute.status, "reason": dispute.reason,
        "statement": dispute.statement, "createdAt": dispute.created_at.isoformat(),
        "canAddEvidence": dispute.status != "resolved" and not dispute.review_locked
        and dispute.evidence.count() < MAX_FILES,
        "evidence": [evidence_data(e) for e in dispute.evidence.order_by("uploaded_at")],
        "resolution": (
            {"decision": dispute.decision, "summary": dispute.resolution_summary,
             "resolvedAt": dispute.resolved_at.isoformat()}
            if dispute.resolved_at else None
        ),
    }


def dispute_view(match, user):
    dispute = getattr(match, "dispute", None)
    result = getattr(match, "result", None)
    if dispute:
        state = dispute.status
        unavailable = None
    elif match.state == Match.State.AWAITING_CONFIRMATION:
        state, unavailable = "eligible", None
    else:
        state = "unavailable"
        unavailable = "cancelled" if match.state == Match.State.CANCELLED else "result-not-ready"
    data = common(match, user)
    data.update({
        "revision": str(match.revision), "disputeState": state,
        "unavailableReason": unavailable,
        "result": {
            "state": (
                "finalized" if match.state == Match.State.COMPLETED else
                "void" if match.state == Match.State.CANCELLED else
                "disputed" if match.state == Match.State.DISPUTED else
                "awaiting-confirmation"
            ),
            "reportedScore": (
                {
                    "playerScore": result.score_a if match.participant_a_id == user.pk else result.score_b,
                    "opponentScore": result.score_b if match.participant_a_id == user.pk else result.score_a,
                } if result else None
            ),
            "finalResult": final_result(match, result, user),
        },
        "policy": {
            "allowedReasons": REASONS, "minStatementLength": 20,
            "maxStatementLength": 1000,
            "evidence": {"enabled": True, "maxFiles": MAX_FILES,
                         "maxFileBytes": MAX_BYTES,
                         "allowedMimeTypes": ["image/jpeg", "image/png", "image/webp"]},
        },
        "dispute": dispute_data(dispute) if dispute else None,
    })
    return data
