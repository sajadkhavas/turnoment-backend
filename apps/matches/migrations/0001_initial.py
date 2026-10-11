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
            name="Match",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "source_kind",
                    models.CharField(
                        choices=[("tournament", "Tournament"), ("challenge", "Challenge")],
                        max_length=12,
                    ),
                ),
                ("source_id", models.CharField(max_length=100)),
                ("game_id", models.CharField(max_length=100)),
                ("game_name", models.CharField(max_length=160)),
                ("competition_title", models.CharField(max_length=200)),
                ("tournament_slug", models.SlugField(blank=True, max_length=160)),
                ("round_label", models.CharField(blank=True, max_length=120)),
                ("opponent_kind", models.CharField(default="player", max_length=8)),
                ("venue_id", models.CharField(blank=True, max_length=100)),
                ("venue_name", models.CharField(blank=True, max_length=160)),
                ("venue_city", models.CharField(blank=True, max_length=100)),
                ("starts_at", models.DateTimeField()),
                ("timezone", models.CharField(default="Asia/Tehran", max_length=64)),
                ("format_label", models.CharField(default="1v1", max_length=100)),
                ("check_in_state", models.CharField(default="not-required", max_length=16)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled"),
                            ("ready", "Ready"),
                            ("live", "Live"),
                            ("awaiting-result", "Awaiting result"),
                            ("awaiting-confirmation", "Awaiting confirmation"),
                            ("disputed", "Disputed"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="scheduled",
                        max_length=24,
                    ),
                ),
                ("revision", models.PositiveIntegerField(default=1)),
                ("min_score", models.PositiveIntegerField(default=0)),
                ("max_score", models.PositiveIntegerField(blank=True, null=True)),
                ("allow_draw", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "participant_a",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="matches_as_a",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "participant_b",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="matches_as_b",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="match",
            constraint=models.UniqueConstraint(
                fields=("source_kind", "source_id"), name="b08_match_source_once"
            ),
        ),
        migrations.AddConstraint(
            model_name="match",
            constraint=models.CheckConstraint(
                condition=~Q(participant_a=F("participant_b")), name="b08_distinct_participants"
            ),
        ),
        migrations.AddConstraint(
            model_name="match",
            constraint=models.CheckConstraint(
                condition=Q(max_score__isnull=True) | Q(max_score__gte=F("min_score")),
                name="b08_score_range",
            ),
        ),
        migrations.AddIndex(
            model_name="match",
            index=models.Index(fields=["participant_a", "-starts_at"], name="b08_a_start_idx"),
        ),
        migrations.AddIndex(
            model_name="match",
            index=models.Index(fields=["participant_b", "-starts_at"], name="b08_b_start_idx"),
        ),
    ]
