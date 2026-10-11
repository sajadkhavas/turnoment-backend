import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Challenge(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"

    class Outcome(models.TextChoices):
        WIN = "win", "Win"
        LOSS = "loss", "Loss"
        DRAW = "draw", "Draw"
        VOID = "void", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="challenges_sent", on_delete=models.PROTECT
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="challenges_received", on_delete=models.PROTECT
    )
    pair_low = models.CharField(max_length=36)
    pair_high = models.CharField(max_length=36)
    game_id = models.CharField(max_length=128)
    game_name = models.CharField(max_length=200)
    format_id = models.CharField(max_length=128)
    format_label = models.CharField(max_length=200)
    note = models.CharField(max_length=240, blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.PENDING)
    revision = models.UUIDField(default=uuid.uuid4)
    match_id = models.CharField(max_length=128, null=True, blank=True, unique=True)
    final_outcome = models.CharField(max_length=8, choices=Outcome.choices, blank=True)
    score_label = models.CharField(max_length=80, blank=True)
    challenger_rating_delta = models.IntegerField(null=True, blank=True)
    opponent_rating_delta = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(challenger=F("opponent")), name="ch_no_self"
            ),
            models.CheckConstraint(
                condition=Q(pair_low__lt=F("pair_high")), name="ch_canonical_pair"
            ),
            models.UniqueConstraint(
                fields=["pair_low", "pair_high", "game_id"],
                condition=Q(state__in=["pending", "accepted"]),
                name="ch_unique_active_pair_game",
            ),
            models.CheckConstraint(
                condition=(
                    Q(state__in=["accepted", "completed"], match_id__isnull=False)
                    | Q(
                        state__in=["pending", "declined", "cancelled", "expired"],
                        match_id__isnull=True,
                    )
                ),
                name="ch_match_state",
            ),
            models.CheckConstraint(
                condition=(
                    Q(state="completed", completed_at__isnull=False)
                    & ~Q(final_outcome="")
                    | ~Q(state="completed")
                    & Q(completed_at__isnull=True)
                    & Q(final_outcome="")
                ),
                name="ch_final_result_state",
            ),
        ]
        indexes = [
            models.Index(fields=["challenger", "-created_at"], name="ch_sent_recent"),
            models.Index(fields=["opponent", "-created_at"], name="ch_recv_recent"),
            models.Index(fields=["state", "expires_at"], name="ch_state_expiry"),
        ]


class ChallengeCommandReceipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    fingerprint = models.CharField(max_length=64)
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["actor", "key"], name="ch_actor_idem_key")
        ]
