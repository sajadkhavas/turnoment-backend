"""Trusted, nonfinancial domain-event entry point; no award endpoint on the web."""

import re

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import AchievementDefinition, AchievementProgress, AchievementProgressEvent

EVENT_KEY = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


@transaction.atomic
def record_progress(*, user, definition_id, event_key: str, increment: int = 1):
    """Exactly-once per (user, definition, event_key), including concurrent replays.

    Events do not infer achievement eligibility. Upstream trusted domain must
    choose definition and event key. No currency, XP or self-claim logic.
    """
    if not isinstance(event_key, str) or not EVENT_KEY.fullmatch(event_key):
        raise ValueError("Invalid event key")
    if type(increment) is not int or increment <= 0:
        raise ValueError("Increment must be a positive integer")
    get_user_model().objects.select_for_update().get(pk=user.pk)
    definition = AchievementDefinition.objects.get(pk=definition_id, is_published=True)
    progress, _ = AchievementProgress.objects.select_for_update().get_or_create(
        user=user, definition=definition, defaults={"current": 0}
    )
    if AchievementProgressEvent.objects.filter(
        user=user, definition=definition, event_key=event_key
    ).exists():
        return progress
    AchievementProgressEvent.objects.create(
        user=user, definition=definition, event_key=event_key
    )
    progress.current = min(definition.target, progress.current + increment)
    if progress.current >= definition.target and progress.unlocked_at is None:
        progress.unlocked_at = timezone.now()
    progress.save(update_fields=["current", "unlocked_at", "updated_at"])
    return progress
