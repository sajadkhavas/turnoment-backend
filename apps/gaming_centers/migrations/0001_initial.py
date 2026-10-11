import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="City",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                    serialize=False)),
                ("slug", models.SlugField(unique=True, max_length=80)),
                ("name", models.CharField(max_length=240)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="GamingCenter",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                    serialize=False)),
                ("public_id", models.SlugField(unique=True, max_length=128)),
                ("publication_state", models.CharField(max_length=12,
                    choices=[("draft", "Draft"), ("published", "Published"), ("hidden", "Hidden")],
                    default="draft")),
                ("name", models.CharField(max_length=240)),
                ("verified", models.BooleanField(default=False)),
                ("city", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                          related_name="centers", to="gaming_centers.city")),
                ("district", models.CharField(max_length=240)),
                ("summary", models.CharField(max_length=420, validators=[
                    django.core.validators.MinLengthValidator(20)
                ])),
                ("description", models.TextField(validators=[
                    django.core.validators.MinLengthValidator(40),
                    django.core.validators.MaxLengthValidator(1800),
                ])),
                ("cover_image", models.URLField(max_length=2048, blank=True)),
                ("street_address", models.CharField(max_length=400, blank=True)),
                ("address_locality", models.CharField(max_length=240, blank=True)),
                ("address_region", models.CharField(max_length=240, blank=True)),
                ("postal_code", models.CharField(max_length=20, blank=True)),
                ("display_address", models.CharField(max_length=500, blank=True)),
                ("show_address", models.BooleanField(default=False)),
                ("business_phone", models.CharField(max_length=32, blank=True)),
                ("show_phone", models.BooleanField(default=False)),
                ("map_url", models.URLField(max_length=2048, blank=True)),
                ("show_map", models.BooleanField(default=False)),
                ("upcoming_tournament_count", models.PositiveIntegerField(
                    null=True, blank=True, default=None)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"indexes": [
                models.Index(fields=["publication_state", "city", "name"],
                    name="center_public_city_idx")
            ],
                "constraints": [models.CheckConstraint(
                    condition=Q(upcoming_tournament_count__gte=0)
                    | Q(upcoming_tournament_count__isnull=True),
                    name="center_nonnegative_tournament_count"
                )]},
        ),
        migrations.CreateModel(
            name="CenterMembership",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                    serialize=False)),
                ("center", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="memberships",
                                             to="gaming_centers.gamingcenter")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="center_memberships",
                                               to=settings.AUTH_USER_MODEL)),
                ("role", models.CharField(max_length=12, choices=[
                    ("owner", "Owner"), ("manager", "Manager"), ("staff", "Staff")])),
                ("is_active", models.BooleanField(default=True)),
                ("joined_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"constraints": [models.UniqueConstraint(
                fields=["center", "user"], name="center_unique_membership"
            )]},
        ),
        migrations.CreateModel(
            name="HostApplication",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                    serialize=False)),
                ("venue_name", models.CharField(max_length=120)),
                ("manager_name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=13)),
                ("city", models.CharField(max_length=80)),
                ("area", models.CharField(max_length=120)),
                ("station_count", models.PositiveSmallIntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(1000)
                ])),
                ("games", models.CharField(max_length=300)),
                ("description", models.CharField(max_length=1200, blank=True)),
                ("state", models.CharField(max_length=12, choices=[
                    ("received", "Received"), ("reviewing", "Reviewing"),
                    ("approved", "Approved"), ("rejected", "Rejected")
                ], default="received")),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now,
                    editable=False)),
                ("client_key", models.CharField(max_length=64, editable=False)),
                ("fingerprint", models.CharField(max_length=64, editable=False)),
                ("bucket_start", models.DateTimeField(editable=False)),
            ],
            options={
                "indexes": [models.Index(fields=["submitted_at"], name="host_retention_time_idx")],
                "constraints": [
                    models.UniqueConstraint(fields=["client_key", "fingerprint", "bucket_start"],
                                            name="host_idempotent_window"),
                    models.CheckConstraint(condition=Q(station_count__gte=1)
                        & Q(station_count__lte=1000), name="host_station_count_range"),
                ],
            },
        ),
        migrations.CreateModel(
            name="HostRateBucket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                            serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64)),
                ("hour_start", models.DateTimeField()),
                ("accepted_count", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"constraints": [
                models.UniqueConstraint(fields=["key", "hour_start"], name="host_unique_rate_hour"),
                models.CheckConstraint(condition=Q(accepted_count__lte=5),
                                       name="host_rate_max_five"),
            ]},
        ),
    ]
