import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("registrations", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="BracketRound",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True,
                    serialize=False
                )),
                ("number", models.PositiveSmallIntegerField()),
                ("title", models.CharField(max_length=100)),
                ("tournament", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="bracket_rounds", to="tournaments.tournament"
                )),
            ],
            options={
                "ordering": ["number"],
                "constraints": [models.UniqueConstraint(
                    fields=("tournament", "number"), name="b05_round_number_unique"
                )],
            },
        ),
        migrations.CreateModel(
            name="BracketMatch",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True,
                    serialize=False
                )),
                ("position", models.PositiveSmallIntegerField()),
                ("label", models.CharField(max_length=100)),
                ("state", models.CharField(
                    choices=[("scheduled", "Scheduled"), ("live", "Live"),
                             ("completed", "Completed")],
                    default="scheduled", max_length=12
                )),
                ("score_a", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("score_b", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("round", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="matches", to="brackets.bracketround"
                )),
                ("side_a", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="bracket_side_a", to="registrations.registration"
                )),
                ("side_b", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="bracket_side_b", to="registrations.registration"
                )),
            ],
            options={
                "ordering": ["position"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("round", "position"), name="b05_match_position_unique"
                    ),
                    models.CheckConstraint(
                        condition=~models.Q(side_a=models.F("side_b"))
                        | models.Q(side_a__isnull=True) | models.Q(side_b__isnull=True),
                        name="b05_no_self_bracket"
                    ),
                ],
            },
        ),
    ]
