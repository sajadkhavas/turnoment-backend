import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F, Q
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    initial = True

    dependencies = [("gaming_centers", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Equipment",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("center", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="equipment", to="gaming_centers.gamingcenter")),
                ("label", models.CharField(max_length=240)),
                ("is_public", models.BooleanField(default=True)),
            ],
            options={"ordering": ["label", "id"], "constraints": [
                models.UniqueConstraint(Lower("label"), "center", name="equip_center_label_ci")
            ]},
        ),
        migrations.CreateModel(
            name="Station",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("center", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="stations", to="gaming_centers.gamingcenter")),
                ("equipment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                                related_name="stations", to="gaming_resources.equipment")),
                ("code", models.CharField(max_length=40)),
                ("state", models.CharField(max_length=12, choices=[
                    ("active", "Active"), ("maintenance", "Maintenance"), ("disabled", "Disabled")
                ], default="active")),
            ],
            options={"constraints": [
                models.UniqueConstraint(fields=["center", "code"], name="station_center_code_unique")
            ]},
        ),
        migrations.CreateModel(
            name="OpeningHour",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                            serialize=False, verbose_name="ID")),
                ("center", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="hours", to="gaming_centers.gamingcenter")),
                ("weekday", models.PositiveSmallIntegerField()),
                ("opens", models.TimeField()),
                ("closes", models.TimeField()),
                ("is_public", models.BooleanField(default=True)),
            ],
            options={"ordering": ["weekday"], "constraints": [
                models.UniqueConstraint(fields=["center", "weekday"], name="center_unique_weekday"),
                models.CheckConstraint(condition=Q(weekday__lte=6), name="center_weekday_range"),
                models.CheckConstraint(condition=Q(closes__gt=F("opens")), name="center_hours_order"),
            ]},
        ),
        migrations.CreateModel(
            name="GalleryImage",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("center", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="gallery", to="gaming_centers.gamingcenter")),
                ("image_url", models.URLField(max_length=2048)),
                ("position", models.PositiveSmallIntegerField()),
                ("is_public", models.BooleanField(default=True)),
            ],
            options={"ordering": ["position"], "constraints": [
                models.UniqueConstraint(fields=["center", "image_url"], name="center_gallery_url_unique"),
                models.UniqueConstraint(fields=["center", "position"], name="center_gallery_pos_unique"),
                models.CheckConstraint(condition=Q(position__lte=7), name="center_gallery_pos_range"),
            ]},
        ),
    ]
