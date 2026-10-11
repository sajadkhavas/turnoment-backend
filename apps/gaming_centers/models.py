import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class City(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=240)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class GamingCenter(models.Model):
    class Publication(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.SlugField(max_length=128, unique=True)
    publication_state = models.CharField(
        max_length=12, choices=Publication.choices, default=Publication.DRAFT
    )
    name = models.CharField(max_length=240)
    verified = models.BooleanField(default=False)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="centers")
    district = models.CharField(max_length=240)
    summary = models.CharField(max_length=420)
    description = models.TextField()
    cover_image = models.URLField(max_length=2048, blank=True)
    street_address = models.CharField(max_length=400, blank=True)
    address_locality = models.CharField(max_length=240, blank=True)
    address_region = models.CharField(max_length=240, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    display_address = models.CharField(max_length=500, blank=True)
    show_address = models.BooleanField(default=False)
    business_phone = models.CharField(max_length=32, blank=True)
    show_phone = models.BooleanField(default=False)
    map_url = models.URLField(max_length=2048, blank=True)
    show_map = models.BooleanField(default=False)
    # Null means tournament aggregation is not wired. Never fabricate zero.
    upcoming_tournament_count = models.PositiveIntegerField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["publication_state", "city", "name"], name="center_public_city_idx")
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(upcoming_tournament_count__gte=0) | Q(upcoming_tournament_count__isnull=True),
                name="center_nonnegative_tournament_count",
            )
        ]

    def __str__(self):
        return self.name


class CenterMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="center_memberships"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["center", "user"], name="center_unique_membership")
        ]


class HostApplication(models.Model):
    class State(models.TextChoices):
        RECEIVED = "received", "Received"
        REVIEWING = "reviewing", "Reviewing"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue_name = models.CharField(max_length=120)
    manager_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=13)
    city = models.CharField(max_length=80)
    area = models.CharField(max_length=120)
    station_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    games = models.CharField(max_length=300)
    description = models.CharField(max_length=1200, blank=True)
    state = models.CharField(
        max_length=12, choices=State.choices, default=State.RECEIVED
    )
    submitted_at = models.DateTimeField(default=timezone.now, editable=False)
    # Hashed request dimensions only; do not store raw source IP.
    client_key = models.CharField(max_length=64, editable=False)
    fingerprint = models.CharField(max_length=64, editable=False)
    bucket_start = models.DateTimeField(editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["client_key", "fingerprint", "bucket_start"],
                name="host_idempotent_window",
            ),
            models.CheckConstraint(
                condition=Q(station_count__gte=1) & Q(station_count__lte=1000),
                name="host_station_count_range",
            ),
        ]
        indexes = [
            models.Index(fields=["submitted_at"], name="host_retention_time_idx")
        ]


class HostRateBucket(models.Model):
    # Database locking makes admissions stricter than cache-backed best effort.
    key = models.CharField(max_length=64)
    hour_start = models.DateTimeField()
    accepted_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "hour_start"], name="host_unique_rate_hour"),
            models.CheckConstraint(
                condition=Q(accepted_count__lte=5), name="host_rate_max_five"
            ),
        ]
