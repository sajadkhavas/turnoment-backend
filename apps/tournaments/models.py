import uuid

from django.db import models
from django.db.models import F, Q


class Tournament(models.Model):
    class Lifecycle(models.TextChoices):
        OPEN = "registration_open", "Registration open"
        FILLING = "filling", "Filling"
        CLOSED = "registration_closed", "Registration closed"
        UPCOMING = "upcoming", "Upcoming"
        CHECK_IN = "check_in", "Check-in"
        LIVE = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Mode(models.TextChoices):
        SOLO = "solo", "Solo"
        TEAM = "team", "Team"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=128, unique=True)
    title = models.CharField(max_length=240)
    description = models.TextField()
    hero_image = models.URLField(blank=True)
    game_key = models.CharField(max_length=128, db_index=True)
    game_slug = models.SlugField(max_length=128)
    game_name = models.CharField(max_length=240)
    game_platform = models.CharField(max_length=80, default="PC")
    game_image = models.URLField(blank=True)
    center_key = models.CharField(max_length=128, db_index=True)
    center_name = models.CharField(max_length=240)
    center_city = models.CharField(max_length=128)
    center_district = models.CharField(max_length=128)
    center_verified = models.BooleanField(default=False)
    center_meta = models.JSONField(default=dict, blank=True)
    starts_at = models.DateTimeField(db_index=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    check_in_opens_at = models.DateTimeField(null=True, blank=True)
    display_date = models.CharField(max_length=120)
    display_time = models.CharField(max_length=120)
    lifecycle = models.CharField(
        max_length=24, choices=Lifecycle.choices, default=Lifecycle.UPCOMING
    )
    capacity = models.PositiveIntegerField()
    registered_count = models.PositiveIntegerField(default=0)
    mode = models.CharField(max_length=8, choices=Mode.choices, default=Mode.SOLO)
    format_label = models.CharField(max_length=100, default="1v1")
    bracket_format_label = models.CharField(max_length=100, default="Single elimination")
    ruleset_key = models.CharField(max_length=128, default="standard")
    rules_version = models.CharField(max_length=60, default="1")
    rules = models.JSONField(default=list, blank=True)
    detail_version = models.CharField(max_length=100, default="1")
    entry_fee = models.PositiveBigIntegerField(default=0)
    fixed_prize = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(capacity__gt=0), name="b05_capacity_positive"),
            models.CheckConstraint(
                condition=Q(registered_count__lte=F("capacity")), name="b05_capacity_bound"
            ),
        ]
        ordering = ["starts_at", "id"]

    @property
    def finance_pending(self):
        return self.entry_fee > 0
