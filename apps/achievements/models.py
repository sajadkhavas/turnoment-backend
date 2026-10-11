import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class AchievementCategory(models.Model):
    id = models.SlugField(primary_key=True, max_length=80)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["id"]


class AchievementDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=128, unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=240)
    category = models.ForeignKey(
        AchievementCategory, on_delete=models.PROTECT, related_name="definitions"
    )
    target = models.PositiveIntegerField(default=1)
    has_progress = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(target__gt=0), name="b06_achievement_target_gt0")
        ]
        ordering = ["position", "code"]


class AchievementProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievement_progress"
    )
    definition = models.ForeignKey(
        AchievementDefinition, on_delete=models.PROTECT, related_name="player_progress"
    )
    current = models.PositiveIntegerField(default=0)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "definition"], name="b06_unique_achievement_progress"
            )
        ]


class AchievementProgressEvent(models.Model):
    """Once-per-user/definition/event dedupe for trusted domain consumers."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    definition = models.ForeignKey(AchievementDefinition, on_delete=models.PROTECT)
    event_key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "definition", "event_key"], name="b06_unique_achievement_event"
            )
        ]
