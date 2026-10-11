# Generated for B07 against Django 6.1.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Challenge",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("pair_low", models.CharField(max_length=36)),
                ("pair_high", models.CharField(max_length=36)),
                ("game_id", models.CharField(max_length=128)),
                ("game_name", models.CharField(max_length=200)),
                ("format_id", models.CharField(max_length=128)),
                ("format_label", models.CharField(max_length=200)),
                ("note", models.CharField(blank=True, max_length=240)),
                ("state", models.CharField(
                    max_length=16, default="pending",
                    choices=[
                        ("pending", "Pending"), ("accepted", "Accepted"),
                        ("declined", "Declined"), ("cancelled", "Cancelled"),
                        ("expired", "Expired"), ("completed", "Completed"),
                    ],
                )),
                ("revision", models.UUIDField(default=uuid.uuid4)),
                ("match_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("final_outcome", models.CharField(
                    blank=True, max_length=8,
                    choices=[("win", "Win"), ("loss", "Loss"), ("draw", "Draw"), ("void", "Void")],
                )),
                ("score_label", models.CharField(blank=True, max_length=80)),
                ("challenger_rating_delta", models.IntegerField(blank=True, null=True)),
                ("opponent_rating_delta", models.IntegerField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("challenger", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="challenges_sent",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("opponent", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="challenges_received",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["challenger", "-created_at"], name="ch_sent_recent"),
                    models.Index(fields=["opponent", "-created_at"], name="ch_recv_recent"),
                    models.Index(fields=["state", "expires_at"], name="ch_state_expiry"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=~Q(challenger=F("opponent")), name="ch_no_self"),
                    models.CheckConstraint(condition=Q(pair_low__lt=F("pair_high")), name="ch_canonical_pair"),
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
                ],
            },
        ),
        migrations.CreateModel(
            name="ChallengeCommandReceipt",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("key", models.CharField(max_length=200)),
                ("fingerprint", models.CharField(max_length=64)),
                ("response", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=["actor", "key"], name="ch_actor_idem_key"),
                ],
            },
        ),
    ]
