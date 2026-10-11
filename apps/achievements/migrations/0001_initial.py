import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="AchievementCategory",
            fields=[
                ("id", models.SlugField(primary_key=True, max_length=80, serialize=False)),
                ("name", models.CharField(max_length=80)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="AchievementDefinition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=128, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(max_length=240)),
                ("target", models.PositiveIntegerField(default=1)),
                ("has_progress", models.BooleanField(default=False)),
                ("is_published", models.BooleanField(default=False)),
                ("position", models.PositiveIntegerField(default=0)),
                ("category",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                        related_name="definitions", to="achievements.achievementcategory")),
            ],
            options={
                "ordering": ["position", "code"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("target__gt", 0)),
                        name="b06_achievement_target_gt0"),
                    models.CheckConstraint(condition=models.Q(("has_progress",
                        True)) | models.Q(("target", 1)), name="b06_binary_target_one"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AchievementProgress",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("current", models.PositiveIntegerField(default=0)),
                ("unlocked_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("definition",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                        related_name="player_progress", to="achievements.achievementdefinition")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="achievement_progress", to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("user",
                "definition"), name="b06_unique_achievement_progress")]},
        ),
        migrations.CreateModel(
            name="AchievementProgressEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("event_key", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("definition",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                        to="achievements.achievementdefinition")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("user",
                "definition", "event_key"), name="b06_unique_achievement_event")]},
        ),
    ]
