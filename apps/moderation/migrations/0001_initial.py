import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="ModerationCase",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("source_type", models.CharField(max_length=24, choices=[
                    ("host_application", "Host application"), ("dispute", "Dispute"),
                    ("managed_content", "Managed content"),
                ])),
                ("source_id", models.CharField(max_length=128, validators=[
                    django.core.validators.RegexValidator("^[A-Za-z0-9_-]{1,128}$"),
                ])),
                ("center_id", models.CharField(max_length=128, blank=True, default="", validators=[
                    django.core.validators.RegexValidator("^[A-Za-z0-9_-]{1,128}$"),
                ])),
                ("title", models.CharField(max_length=160)),
                ("status", models.CharField(max_length=16, default="open", choices=[
                    ("open", "Open"), ("in_review", "In review"), ("closed", "Closed"),
                ])),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-opened_at", "-id"],
                "indexes": [
                    models.Index(fields=["source_type", "status"], name="mod_source_status_idx"),
                    models.Index(fields=["center_id", "status"], name="mod_center_status_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=["source_type", "source_id"], name="mod_source_unique"),
                    models.CheckConstraint(condition=Q(source_type__in=["host_application", "dispute", "managed_content"]), name="mod_source_allowed"),
                    models.CheckConstraint(condition=Q(status__in=["open", "in_review", "closed"]), name="mod_status_allowed"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ModerationDecision",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("from_status", models.CharField(max_length=16, choices=[
                    ("open", "Open"), ("in_review", "In review"), ("closed", "Closed"),
                ])),
                ("to_status", models.CharField(max_length=16, choices=[
                    ("open", "Open"), ("in_review", "In review"), ("closed", "Closed"),
                ])),
                ("note", models.CharField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(to="moderation.moderationcase", related_name="decisions", on_delete=django.db.models.deletion.PROTECT)),
                ("actor", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                "ordering": ["created_at", "id"],
                "constraints": [
                    models.CheckConstraint(
                        condition=Q(from_status="open", to_status="in_review")
                        | Q(from_status="in_review", to_status="closed"),
                        name="mod_decision_transition_valid",
                    ),
                ],
            },
        ),
    ]
