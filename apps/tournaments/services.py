from django.db import transaction
from django.utils import timezone

from .models import Tournament

ALLOWED_TRANSITIONS = {
    Tournament.Lifecycle.UPCOMING: {Tournament.Lifecycle.OPEN, Tournament.Lifecycle.CANCELLED},
    Tournament.Lifecycle.OPEN: {
        Tournament.Lifecycle.FILLING, Tournament.Lifecycle.CLOSED, Tournament.Lifecycle.CANCELLED
    },
    Tournament.Lifecycle.FILLING: {
        Tournament.Lifecycle.CLOSED, Tournament.Lifecycle.CANCELLED
    },
    Tournament.Lifecycle.CLOSED: {
        Tournament.Lifecycle.CHECK_IN, Tournament.Lifecycle.CANCELLED
    },
    Tournament.Lifecycle.CHECK_IN: {
        Tournament.Lifecycle.LIVE, Tournament.Lifecycle.CANCELLED
    },
    Tournament.Lifecycle.LIVE: {Tournament.Lifecycle.COMPLETED},
    Tournament.Lifecycle.COMPLETED: set(),
    Tournament.Lifecycle.CANCELLED: set(),
}


@transaction.atomic
def transition_tournament(tournament_id, target):
    tournament = Tournament.objects.select_for_update().get(pk=tournament_id)
    if tournament.lifecycle == target:
        return tournament
    if target not in ALLOWED_TRANSITIONS[tournament.lifecycle]:
        raise ValueError("Invalid tournament lifecycle transition")
    tournament.lifecycle = target
    tournament.save(update_fields=["lifecycle"])
    return tournament


def availability(tournament):
    if tournament.finance_pending:
        return "ineligible"
    if tournament.lifecycle == Tournament.Lifecycle.UPCOMING:
        return "upcoming"
    if tournament.lifecycle not in {
        Tournament.Lifecycle.OPEN, Tournament.Lifecycle.FILLING
    }:
        return "closed"
    if (
        tournament.registration_closes_at
        and timezone.now() >= tournament.registration_closes_at
    ):
        return "closed"
    if tournament.registered_count >= tournament.capacity:
        return "full"
    return "available"
