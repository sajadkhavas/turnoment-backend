"""Prevent ambiguous overlapping B09 seasons at the PostgreSQL boundary."""

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rankings", "0001_initial")]

    operations = [
        migrations.AddConstraint(
            model_name="season",
            constraint=ExclusionConstraint(
                name="b09_no_season_overlap",
                expressions=[
                    (
                        models.Func(
                            "starts_at", "ends_at", RangeBoundary(),
                            function="TSTZRANGE", output_field=DateTimeRangeField(),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
        ),
    ]
