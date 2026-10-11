import uuid

from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tournament",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True,
                    serialize=False
                )),
                ("slug", models.SlugField(max_length=128, unique=True)),
                ("title", models.CharField(max_length=240)),
                ("description", models.TextField()),
                ("hero_image", models.URLField(blank=True)),
                ("game_key", models.CharField(db_index=True, max_length=128)),
                ("game_slug", models.SlugField(max_length=128)),
                ("game_name", models.CharField(max_length=240)),
                ("game_platform", models.CharField(default="PC", max_length=80)),
                ("game_image", models.URLField(blank=True)),
                ("center_key", models.CharField(db_index=True, max_length=128)),
                ("center_name", models.CharField(max_length=240)),
                ("center_city", models.CharField(max_length=128)),
                ("center_district", models.CharField(max_length=128)),
                ("center_verified", models.BooleanField(default=False)),
                ("center_meta", models.JSONField(blank=True, default=dict)),
                ("starts_at", models.DateTimeField(db_index=True)),
                ("registration_closes_at", models.DateTimeField(blank=True, null=True)),
                ("check_in_opens_at", models.DateTimeField(blank=True, null=True)),
                ("display_date", models.CharField(max_length=120)),
                ("display_time", models.CharField(max_length=120)),
                ("lifecycle", models.CharField(
                    choices=[("registration_open", "Registration open"), ("filling", "Filling"),
                             ("registration_closed", "Registration closed"),
                             ("upcoming", "Upcoming"),
                             ("check_in", "Check-in"), ("in_progress", "In progress"),
                             ("completed", "Completed"), ("cancelled", "Cancelled")],
                    default="upcoming", max_length=24
                )),
                ("capacity", models.PositiveIntegerField()),
                ("registered_count", models.PositiveIntegerField(default=0)),
                ("mode", models.CharField(choices=[("solo", "Solo"), ("team", "Team")],
                                          default="solo", max_length=8)),
                ("format_label", models.CharField(default="1v1", max_length=100)),
                ("bracket_format_label", models.CharField(
                    default="Single elimination", max_length=100
                )),
                ("ruleset_key", models.CharField(default="standard", max_length=128)),
                ("rules_version", models.CharField(default="1", max_length=60)),
                ("rules", models.JSONField(blank=True, default=list)),
                ("detail_version", models.CharField(default="1", max_length=100)),
                ("entry_fee", models.PositiveBigIntegerField(default=0)),
                ("fixed_prize", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["starts_at", "id"],
                "constraints": [
                    models.CheckConstraint(
                        condition=Q(capacity__gt=0), name="b05_capacity_positive"
                    ),
                    models.CheckConstraint(
                        condition=Q(registered_count__lte=F("capacity")),
                        name="b05_capacity_bound"
                    ),
                ],
            },
        ),
    ]
