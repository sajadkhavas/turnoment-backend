import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [("games", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Ruleset",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ("key", models.CharField(
                    max_length=96,
                    validators=[django.core.validators.RegexValidator(
                        "^[a-z0-9]+(?:-[a-z0-9]+)*$"
                    )],
                )),
                ("revision", models.CharField(max_length=40)),
                ("publication_state", models.CharField(
                    choices=[
                        ("draft", "Draft"), ("published", "Published"), ("archived", "Archived"),
                    ], default="draft", max_length=12,
                )),
                ("title", models.CharField(max_length=180)),
                ("summary", models.CharField(max_length=1200)),
                ("effective_on", models.DateField(blank=True, null=True)),
                ("sections", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("game", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="rulesets", to="games.game",
                )),
            ],
            options={
                "ordering": ("key", "-created_at"),
                "indexes": [
                    models.Index(
                        fields=["publication_state", "key"], name="rulesets_public_key_idx"
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=["key", "revision"], name="ruleset_key_rev_unique"
                    ),
                    models.UniqueConstraint(
                        fields=["key"], condition=Q(publication_state="published"),
                        name="ruleset_one_published_key"
                    ),
                    models.CheckConstraint(
                        condition=Q(publication_state__in=["draft", "published", "archived"]),
                        name="ruleset_publication_valid"
                    ),
                ],
            },
        )
    ]
