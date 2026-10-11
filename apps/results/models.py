import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class MatchResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField("matches.Match", on_delete=models.PROTECT, related_name="result")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_results"
    )
    idempotency_key = models.CharField(max_length=200)
    score_a = models.PositiveIntegerField()
    score_b = models.PositiveIntegerField()
    reported_at = models.DateTimeField(auto_now_add=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_results",
        null=True,
        blank=True,
    )
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(finalized_at__isnull=True) | Q(confirmed_by__isnull=False),
                name="b08_confirm_before_final",
            ),
        ]


class FinalizedResultEvent(models.Model):
    """Durable, exactly-once authoritative event for B09. No ranking formula here."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField(
        "matches.Match", on_delete=models.PROTECT, related_name="finalization_event"
    )
    result = models.OneToOneField(
        MatchResult, on_delete=models.PROTECT, related_name="finalization_event"
    )
    score_a = models.PositiveIntegerField()
    score_b = models.PositiveIntegerField()
    player_a_id = models.UUIDField()
    player_b_id = models.UUIDField()
    finalized_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["finalized_at"], name="b08_final_event_idx")]
