import django.contrib.postgres.indexes
import django.contrib.postgres.search
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q

import apps.games.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Game",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.games.models.new_game_id,
                        max_length=128,
                        primary_key=True,
                        serialize=False,
                        validators=[django.core.validators.RegexValidator(
                            "^[A-Za-z0-9_-]{1,128}$"
                        )],
                    ),
                ),
                (
                    "slug",
                    models.CharField(
                        max_length=128,
                        unique=True,
                        validators=[django.core.validators.RegexValidator(
                            "^[a-z0-9]+(?:-[a-z0-9]+)*$"
                        )],
                    ),
                ),
                (
                    "publication_state",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("published", "Published"),
                            ("archived", "Archived"),
                        ],
                        default="draft",
                        max_length=12,
                    ),
                ),
                ("name", models.CharField(max_length=240)),
                ("short_name", models.CharField(max_length=240)),
                (
                    "description",
                    models.TextField(validators=[django.core.validators.MinLengthValidator(20), django.core.validators.MaxLengthValidator(700)]),
                ),
                ("platforms", models.JSONField(default=list)),
                ("cover_image", models.CharField(blank=True, max_length=2048, null=True)),
                ("hero_image", models.CharField(blank=True, max_length=2048, null=True)),
                ("detail_version", models.CharField(default="1", max_length=80)),
                ("seo_title", models.CharField(blank=True, max_length=180)),
                ("seo_description", models.CharField(blank=True, max_length=320)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("sort_order", "id"),
                "indexes": [
                    models.Index(
                        fields=["publication_state", "sort_order", "id"],
                        name="games_public_order_idx",
                    ),
                    django.contrib.postgres.indexes.GinIndex(
                        django.contrib.postgres.search.SearchVector(
                            "name", "short_name", "description", config="simple"
                        ),
                        name="games_public_search_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=Q(publication_state__in=["draft", "published", "archived"]),
                        name="games_publication_valid",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="CompetitiveFormat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID")),
                ("key", models.CharField(
                    max_length=96,
                    validators=[django.core.validators.RegexValidator(
                        "^[a-z0-9]+(?:-[a-z0-9]+)*$"
                    )],
                )),
                ("label", models.CharField(max_length=240)),
                (
                    "description",
                    models.TextField(validators=[django.core.validators.MinLengthValidator(1)]),
                ),
                ("team_size", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("game", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="competitive_formats",
                    to="games.game",
                )),
            ],
            options={
                "ordering": ("sort_order", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=["game", "key"], name="games_format_key_unique"
                    ),
                    models.CheckConstraint(
                        condition=Q(team_size__isnull=True) | Q(team_size__gt=0),
                        name="games_format_team_size_positive",
                    ),
                ],
            },
        ),
    ]
