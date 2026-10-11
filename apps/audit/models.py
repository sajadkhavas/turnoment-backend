"""Private append-only-in-service audit records and durable integration event outbox."""

import uuid

from django.conf import settings
from django.db import models


class AuditRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=80)
    idempotency_key = models.CharField(max_length=200)
    action = models.CharField(max_length=120)
    subject_type = models.CharField(max_length=80)
    subject_id = models.CharField(max_length=128)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "idempotency_key"], name="audit_source_key_once",
            ),
            models.CheckConstraint(condition=~models.Q(action=""), name="audit_action_nonempty"),
        ]
        indexes = [
            models.Index(fields=["subject_type", "subject_id", "created_at"], name="audit_subject_idx"),
        ]


class DomainEvent(models.Model):
    """Durable event truth; consumer delivery/acknowledgement is B99/B10-owned."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=80)
    idempotency_key = models.CharField(max_length=200)
    event_type = models.CharField(max_length=120)
    subject_type = models.CharField(max_length=80)
    subject_id = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "idempotency_key"], name="event_source_key_once",
            ),
            models.CheckConstraint(condition=~models.Q(event_type=""), name="event_type_nonempty"),
        ]
        indexes = [
            models.Index(
                fields=["subject_type", "subject_id", "occurred_at"], name="event_subject_idx",
            ),
        ]
