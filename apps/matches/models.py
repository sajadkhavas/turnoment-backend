import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Match(models.Model):
    """Authoritative match identity; source owners call create_match_for_source()."""

    class Source(models.TextChoices):
        TOURNAMENT = "tournament", "Tournament"
        CHALLENGE = "challenge", "Challenge"

    class State(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        READY = "ready", "Ready"
        LIVE = "live", "Live"
        AWAITING_RESULT = "awaiting-result", "Awaiting result"
        AWAITING_CONFIRMATION = "awaiting-confirmation", "Awaiting confirmation"
        DISPUTED = "disputed", "Disputed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_kind = models.CharField(max_length=12, choices=Source.choices)
    source_id = models.CharField(max_length=100)
    participant_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="matches_as_a"
    )
    participant_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="matches_as_b"
    )
    game_id = models.CharField(max_length=100)
    game_name = models.CharField(max_length=160)
    competition_title = models.CharField(max_length=200)
    tournament_slug = models.SlugField(max_length=160, blank=True)
    round_label = models.CharField(max_length=120, blank=True)
    opponent_kind = models.CharField(max_length=8, default="player")
    venue_id = models.CharField(max_length=100, blank=True)
    venue_name = models.CharField(max_length=160, blank=True)
    venue_city = models.CharField(max_length=100, blank=True)
    starts_at = models.DateTimeField()
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    format_label = models.CharField(max_length=100, default="1v1")
    check_in_state = models.CharField(max_length=16, default="not-required")
    state = models.CharField(max_length=24, choices=State.choices, default=State.SCHEDULED)
    revision = models.PositiveIntegerField(default=1)
    min_score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(null=True, blank=True)
    allow_draw = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_kind", "source_id"], name="b08_match_source_once"
            ),
            models.CheckConstraint(
                condition=~Q(participant_a=F("participant_b")), name="b08_distinct_participants"
            ),
            models.CheckConstraint(
                condition=Q(max_score__isnull=True) | Q(max_score__gte=F("min_score")),
                name="b08_score_range",
            ),
        ]
        indexes = [
            models.Index(fields=["participant_a", "-starts_at"], name="b08_a_start_idx"),
            models.Index(fields=["participant_b", "-starts_at"], name="b08_b_start_idx"),
        ]

    def has_participant(self, user):
        return user.is_authenticated and user.pk in (self.participant_a_id, self.participant_b_id)
