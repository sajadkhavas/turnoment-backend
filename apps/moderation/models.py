import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


class ModerationCase(models.Model):
    class Source(models.TextChoices):
        HOST_APPLICATION = "host_application", "Host application"
        DISPUTE = "dispute", "Dispute"
        MANAGED_CONTENT = "managed_content", "Managed content"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(max_length=24, choices=Source.choices)
    source_id = models.CharField(
        max_length=128,
        validators=[RegexValidator(r"^[A-Za-z0-9_-]{1,128}$")],
    )
    center_id = models.CharField(
        max_length=128, blank=True, default="",
        validators=[RegexValidator(r"^[A-Za-z0-9_-]{1,128}$")],
    )
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-opened_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"], name="mod_source_unique"
            ),
            models.CheckConstraint(
                condition=Q(source_type__in=["host_application", "dispute", "managed_content"]),
                name="mod_source_allowed",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["open", "in_review", "closed"]),
                name="mod_status_allowed",
            ),
        ]
        indexes = [
            models.Index(fields=["source_type", "status"], name="mod_source_status_idx"),
            models.Index(fields=["center_id", "status"], name="mod_center_status_idx"),
        ]


class ModerationDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        ModerationCase, on_delete=models.PROTECT, related_name="decisions"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_status = models.CharField(max_length=16, choices=ModerationCase.Status.choices)
    to_status = models.CharField(max_length=16, choices=ModerationCase.Status.choices)
    note = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(from_status="open", to_status="in_review")
                    | Q(from_status="in_review", to_status="closed")
                ),
                name="mod_decision_transition_valid",
            ),
        ]
