from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Match

_ALLOWED = {
    Match.State.SCHEDULED: {Match.State.READY, Match.State.CANCELLED},
    Match.State.READY: {Match.State.LIVE, Match.State.AWAITING_RESULT, Match.State.CANCELLED},
    Match.State.LIVE: {Match.State.AWAITING_RESULT, Match.State.CANCELLED},
}


@transaction.atomic
def create_match_for_source(
    *,
    source_kind,
    source_id,
    participant_a,
    participant_b,
    game_id,
    game_name,
    competition_title,
    starts_at,
    **snapshots,
):
    """B05/B07 seam. Call only after their source eligibility/authorization checks.

    Exactly one match per source. Repeated same-source calls return the same identity;
    conflicting source reuse fails closed. The source owner manages its own transaction.
    """
    if (
        source_kind not in Match.Source.values
        or not source_id
        or participant_a.pk == participant_b.pk
    ):
        raise ValidationError("Invalid match source or participants")
    if timezone.is_naive(starts_at):
        raise ValidationError("starts_at must have a timezone")
    if not all((game_id, game_name, competition_title)):
        raise ValidationError("Missing match identity")
    allowed = {
        "tournament_slug",
        "round_label",
        "venue_id",
        "venue_name",
        "venue_city",
        "timezone",
        "format_label",
        "check_in_state",
        "min_score",
        "max_score",
        "allow_draw",
    }
    if set(snapshots) - allowed:
        raise ValidationError("Unknown match snapshot")
    match, created = Match.objects.get_or_create(
        source_kind=source_kind,
        source_id=source_id,
        defaults={
            "participant_a": participant_a,
            "participant_b": participant_b,
            "game_id": game_id,
            "game_name": game_name,
            "competition_title": competition_title,
            "starts_at": starts_at,
            **snapshots,
        },
    )
    if not created and (
        match.participant_a_id != participant_a.pk
        or match.participant_b_id != participant_b.pk
        or match.game_id != game_id
        or match.game_name != game_name
        or match.competition_title != competition_title
        or match.starts_at != starts_at
        or any(getattr(match, field) != value for field, value in snapshots.items())
    ):
        raise ValidationError("Source already bound to a different match")
    return match


@transaction.atomic
def advance_match(match_id, target_state):
    """Explicit source/operator seam; never infer completion from elapsed wall time."""
    match = Match.objects.select_for_update().get(pk=match_id)
    if target_state == match.state:
        return match
    if target_state not in _ALLOWED.get(match.state, set()):
        raise ValidationError("Invalid match transition")
    match.state = target_state
    match.revision += 1
    match.save(update_fields=["state", "revision"])
    return match
