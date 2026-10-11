from django.db import transaction

from apps.registrations.models import Registration

from .models import BracketMatch, BracketRound


@transaction.atomic
def publish_round(*, tournament, number, title, pairings):
    """B08 handoff: seeded registrations only; no match result mutations here."""
    from apps.tournaments.models import Tournament

    locked = Tournament.objects.select_for_update().get(pk=tournament.pk)
    if locked.lifecycle not in {
        Tournament.Lifecycle.CLOSED, Tournament.Lifecycle.CHECK_IN
    }:
        raise ValueError("Bracket cannot be seeded in this lifecycle")
    if not 1 <= number <= 99 or not 1 <= len(pairings) <= 4:
        raise ValueError("Invalid bracket round size")
    registration_ids = {item for pair in pairings for item in pair if item is not None}
    present = set(
        Registration.objects.filter(
            tournament=locked, status=Registration.Status.CONFIRMED,
            pk__in=registration_ids
        ).values_list("pk", flat=True)
    )
    if registration_ids != present:
        raise ValueError("Cross-tournament or unconfirmed participant")
    if any(a is None and b is None for a, b in pairings):
        raise ValueError("Bracket pair cannot be empty")
    if any(a is not None and a == b for a, b in pairings):
        raise ValueError("Same player cannot occupy both sides")
    participants = [
        participant for pair in pairings for participant in pair
        if participant is not None
    ]
    if len(participants) != len(set(participants)):
        raise ValueError("Registration may appear only once per bracket round")
    round_obj = BracketRound.objects.create(
        tournament=locked, number=number, title=title
    )
    for index, (a, b) in enumerate(pairings, start=1):
        BracketMatch.objects.create(
            round=round_obj, position=index, label=f"Match {index}",
            side_a_id=a, side_b_id=b
        )
    return round_obj
