import uuid

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.matches.models import Match

from .models import FinalizedResultEvent, MatchResult


def lock_private_match(match_id, user):
    match = Match.objects.select_for_update().filter(pk=match_id).first()
    if match is None or not match.has_participant(user):
        raise PermissionDenied("Not a match participant")
    return match


def score_errors(match, a, b):
    errors = {}
    for field, value in (("playerScore", a), ("opponentScore", b)):
        if (
            type(value) is not int
            or value < match.min_score
            or (match.max_score is not None and value > match.max_score)
        ):
            errors[field] = "Invalid score"
    if not errors and not match.allow_draw and a == b:
        errors["form"] = "Draw not allowed"
    return errors


@transaction.atomic
def submit_score(match_id, user, revision, player_score, opponent_score, key):
    match = lock_private_match(match_id, user)
    from .projections import receipt

    result = MatchResult.objects.filter(match=match).first()
    if result:
        if result.reported_by_id == user.pk and result.idempotency_key == key:
            a, b = (
                (result.score_a, result.score_b)
                if match.participant_a_id == user.pk
                else (result.score_b, result.score_a)
            )
            if (a, b) != (player_score, opponent_score):
                return {
                    "outcome": "validation_error",
                    "fields": {"form": "Idempotency key conflict"},
                }
        return receipt(match, result, user, replay=True)
    if str(match.revision) != revision:
        return {"outcome": "stale", "revision": str(match.revision)}
    if match.state != Match.State.AWAITING_RESULT:
        reason = {
            Match.State.DISPUTED: "disputed",
            Match.State.COMPLETED: "finalized",
            Match.State.CANCELLED: "cancelled",
        }.get(match.state, "not-reportable")
        return {"outcome": "unavailable", "reason": reason}
    errors = score_errors(match, player_score, opponent_score)
    if errors:
        return {"outcome": "validation_error", "fields": errors}
    a, b = (
        (player_score, opponent_score)
        if match.participant_a_id == user.pk
        else (opponent_score, player_score)
    )
    result = MatchResult.objects.create(
        match=match, reported_by=user, idempotency_key=key, score_a=a, score_b=b
    )
    match.state = Match.State.AWAITING_CONFIRMATION
    match.revision += 1
    match.save(update_fields=["state", "revision"])
    return receipt(match, result, user)


def finalize_locked(match, result, confirmer):
    """Call inside transaction with locked Match row."""
    if match.state == Match.State.COMPLETED:
        return FinalizedResultEvent.objects.get(match=match)
    if match.state not in {Match.State.AWAITING_CONFIRMATION, Match.State.DISPUTED}:
        raise ValueError("Invalid finalization transition")
    if result.finalized_at is None:
        result.confirmed_by = confirmer
        result.finalized_at = timezone.now()
        result.save(update_fields=["confirmed_by", "finalized_at"])
    event, _ = FinalizedResultEvent.objects.get_or_create(
        match=match,
        defaults={
            "result": result,
            "score_a": result.score_a,
            "score_b": result.score_b,
            "player_a_id": match.participant_a_id,
            "player_b_id": match.participant_b_id,
            "finalized_at": result.finalized_at,
        },
    )
    match.state = Match.State.COMPLETED
    match.revision += 1
    match.save(update_fields=["state", "revision"])
    if match.source_kind == Match.Source.CHALLENGE:
        # B07 owns the invitation lifecycle. Existing B08-origin test fixtures
        # without a corresponding invitation remain compatible; real B07-bound
        # matches are finalized in the same database transaction.
        from apps.challenges.models import Challenge
        from apps.challenges.services import record_finalized_match

        try:
            challenge_id = uuid.UUID(match.source_id)
        except (ValueError, TypeError, AttributeError):
            challenge_id = None
        challenge = Challenge.objects.filter(pk=challenge_id).first() if challenge_id else None
        if challenge is not None:
            score_a, score_b = event.score_a, event.score_b
            result_label = f"{score_a} - {score_b}"
            challenger_outcome = (
                "win" if score_a > score_b else "loss" if score_a < score_b else "draw"
            )
            record_finalized_match(
                str(challenge.pk), str(match.pk),
                challenger_outcome=challenger_outcome,
                score_label=result_label,
                completed_at=event.finalized_at,
            )
    return event


@transaction.atomic
def confirm_score(match_id, user, revision, player_score, opponent_score):
    match = lock_private_match(match_id, user)
    result = MatchResult.objects.filter(match=match).first()
    if match.state == Match.State.COMPLETED and result:
        return {
            "outcome": "already_finalized",
            "eventId": str(FinalizedResultEvent.objects.get(match=match).pk),
        }
    if revision != str(match.revision):
        return {"outcome": "stale", "revision": str(match.revision)}
    if (
        match.state != Match.State.AWAITING_CONFIRMATION
        or result is None
        or result.reported_by_id == user.pk
    ):
        return {"outcome": "unavailable"}
    a, b = (
        (result.score_a, result.score_b)
        if match.participant_a_id == user.pk
        else (result.score_b, result.score_a)
    )
    if (a, b) != (player_score, opponent_score):
        return {"outcome": "score_mismatch"}
    event = finalize_locked(match, result, user)
    return {"outcome": "finalized", "eventId": str(event.pk), "revision": str(match.revision)}
