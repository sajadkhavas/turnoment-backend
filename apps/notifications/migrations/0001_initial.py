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
            name="Notification",
            fields=[
                ("id", models.UUIDField(
                    primary_key=True, default=uuid.uuid4,
                    editable=False, serialize=False,
                )),
                ("event_key", models.CharField(max_length=160)),
                ("kind", models.CharField(max_length=16, choices=[
                    ("tournament", "Tournament"), ("match", "Match"), ("challenge", "Challenge"),
                    ("account", "Account"), ("system", "System"),
                ])),
                ("title", models.CharField(max_length=160)),
                ("body", models.CharField(max_length=500)),
                ("target_kind", models.CharField(max_length=32, blank=True, default="", choices=[
                    ("", "No target"), ("my-tournaments", "My tournaments"),
                    ("my-matches", "My matches"), ("tournament-detail", "Tournament detail"),
                    ("result-submission", "Result submission"), ("match-dispute", "Match dispute"),
                    ("player-profile", "Player profile"),
                ])),
                ("target_id", models.CharField(max_length=128, blank=True, default="", validators=[
                    django.core.validators.RegexValidator("^[A-Za-z0-9_-]{1,128}$"),
                ])),
                ("occurred_at", models.DateTimeField()),
                ("read_at", models.DateTimeField(null=True, blank=True)),
                ("recipient", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                )),
            ],
            options={
                "ordering": ["-occurred_at", "-id"],
                "indexes": [
                    models.Index(fields=["recipient", "-occurred_at"], name="notify_rec_time_idx"),
                    models.Index(fields=["recipient", "read_at"], name="notify_rec_read_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=["recipient", "event_key"],
                        name="notify_recipient_event_unique",
                    ),
                    models.CheckConstraint(
                        condition=Q(kind__in=[
                            "tournament", "match", "challenge", "account", "system",
                        ]),
                        name="notify_kind_allowed",
                    ),
                    models.CheckConstraint(condition=(
                        (
                            Q(target_kind__in=[
                                "", "my-tournaments", "my-matches", "player-profile",
                            ]) & Q(target_id="")
                        )
                        | (
                            Q(target_kind__in=[
                                "tournament-detail", "result-submission", "match-dispute",
                            ]) & ~Q(target_id="")
                        )
                    ), name="notify_target_shape_valid"),
                ],
            },
        ),
    ]
