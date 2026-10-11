import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditRecord",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ("source", models.CharField(max_length=80)),
                ("idempotency_key", models.CharField(max_length=200)),
                ("action", models.CharField(max_length=120)),
                ("subject_type", models.CharField(max_length=80)),
                ("subject_id", models.CharField(max_length=128)),
                ("details", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "indexes": [models.Index(\n                    fields=["subject_type", "subject_id", "created_at"],\n                    name="audit_subject_idx",\n                )],
                "constraints": [
                    models.UniqueConstraint(\n                        fields=("source", "idempotency_key"), name="audit_source_key_once",\n                    ),
                    models.CheckConstraint(\n                        condition=~models.Q(action=""), name="audit_action_nonempty",\n                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DomainEvent",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ("source", models.CharField(max_length=80)),
                ("idempotency_key", models.CharField(max_length=200)),
                ("event_type", models.CharField(max_length=120)),
                ("subject_type", models.CharField(max_length=80)),
                ("subject_id", models.CharField(max_length=128)),
                ("payload", models.JSONField(default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "indexes": [models.Index(\n                    fields=["subject_type", "subject_id", "occurred_at"],\n                    name="event_subject_idx",\n                )],
                "constraints": [
                    models.UniqueConstraint(\n                        fields=("source", "idempotency_key"), name="event_source_key_once",\n                    ),
                    models.CheckConstraint(\n                        condition=~models.Q(event_type=""), name="event_type_nonempty",\n                    ),
                ],
            },
        ),
    ]
