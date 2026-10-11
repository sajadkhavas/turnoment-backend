import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


class Notification(models.Model):
    class Kind(models.TextChoices):
        TOURNAMENT = "tournament", "Tournament"
        MATCH = "match", "Match"
        CHALLENGE = "challenge", "Challenge"
        ACCOUNT = "account", "Account"
        SYSTEM = "system", "System"

    class Target(models.TextChoices):
        NONE = "", "No target"
        MY_TOURNAMENTS = "my-tournaments", "My tournaments"
        MY_MATCHES = "my-matches", "My matches"
        TOURNAMENT = "tournament-detail", "Tournament detail"
        RESULT = "result-submission", "Result submission"
        DISPUTE = "match-dispute", "Match dispute"
        PROFILE = "player-profile", "Player profile"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_key = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=500)
    target_kind = models.CharField(max_length=32, choices=Target.choices, blank=True, default="")
    target_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[A-Za-z0-9_-]{1,128}$")],
    )
    occurred_at = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_key"], name="notify_recipient_event_unique"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["tournament", "match", "challenge", "account", "system"]),
                name="notify_kind_allowed",
            ),
            models.CheckConstraint(
                condition=(
                    Q(target_kind__in=["", "my-tournaments", "my-matches", "player-profile"])
                    & Q(target_id="")
                ) | (
                    Q(target_kind__in=["tournament-detail", "result-submission", "match-dispute"])
                    & ~Q(target_id="")
                ),
                name="notify_target_shape_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["recipient", "-occurred_at"], name="notify_rec_time_idx"),
            models.Index(fields=["recipient", "read_at"], name="notify_rec_read_idx"),
        ]
