import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEW = "under-review", "Under review"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField("matches.Match", on_delete=models.PROTECT, related_name="dispute")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="raised_disputes"
    )
    idempotency_key = models.CharField(max_length=200)
    reason = models.CharField(max_length=32)
    statement = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    review_locked = models.BooleanField(default=False)
    decision = models.CharField(max_length=16, blank=True)
    resolution_summary = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(status="resolved", resolved_at__isnull=False)
                | ~Q(status="resolved", resolved_at__isnull=True),
                name="b08_dispute_resolution_ts",
            ),
        ]


class DisputeEvidence(models.Model):
    """Opaque quarantined bytes; no storage URL, no execution/inline serving."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(Dispute, on_delete=models.PROTECT, related_name="evidence")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dispute_evidence"
    )
    idempotency_key = models.CharField(max_length=200)
    file_name = models.CharField(max_length=160)
    content_type = models.CharField(max_length=32)
    size_bytes = models.PositiveIntegerField()
    quarantined_bytes = models.BinaryField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dispute", "uploaded_by", "idempotency_key"],
                name="b08_evidence_retry_unique",
            ),
            models.CheckConstraint(condition=Q(size_bytes__gt=0), name="b08_evidence_nonempty"),
        ]
