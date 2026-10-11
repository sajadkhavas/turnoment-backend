from django.db import transaction
from django.utils import timezone

from apps.registrations.models import Registration
from apps.tournaments.models import Tournament

from .models import CheckIn


@transaction.atomic
def check_in(*, tournament, user):
    # Same parent lock as registration/lifecycle to serialize state changes.
    tournament = Tournament.objects.select_for_update().get(pk=tournament.pk)
    registration = (
        Registration.objects.select_for_update()
        .filter(tournament=tournament, user=user, status=Registration.Status.CONFIRMED)
        .first()
    )
    if registration is None:
        return {"outcome": "unavailable", "reason": "not_registered"}
    old = CheckIn.objects.filter(registration=registration).first()
    if old:
        return {"outcome": "completed", "checkedAt": old.checked_at.isoformat()}
    now = timezone.now()
    if (
        tournament.lifecycle not in {
            Tournament.Lifecycle.CHECK_IN, Tournament.Lifecycle.CLOSED,
            Tournament.Lifecycle.UPCOMING
        }
        or not tournament.check_in_opens_at
        or now < tournament.check_in_opens_at
        or now >= tournament.starts_at
    ):
        return {"outcome": "unavailable", "reason": "not_open"}
    created = CheckIn.objects.create(registration=registration)
    return {"outcome": "completed", "checkedAt": created.checked_at.isoformat()}
