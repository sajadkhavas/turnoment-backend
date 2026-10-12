import uuid

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Q


class Season(models.Model):
    """Explicit published competitive window; no guessed default seasons."""

    slug = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="b09_season_window"
            ),
            ExclusionConstraint(
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
        ]
        ordering = ["-starts_at", "slug"]


class PublicRankingIdentity(models.Model):
    """B09 publication opt-in; never infer public username from mutable gamer_tag."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, primary_key=True,
        on_delete=models.PROTECT, related_name="ranking_identity",
    )
    username = models.CharField(max_length=64, unique=True)
    city = models.ForeignKey(
        "gaming_centers.City", on_delete=models.PROTECT, related_name="ranking_identities"
    )
    is_published = models.BooleanField(default=False)
    search_visibility = models.CharField(
        max_length=12,
        choices=[("indexable", "Indexable"), ("noindex", "Noindex")],
        default="noindex",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(username__regex=r"^[a-z0-9][a-z0-9_-]{1,63}$"),
                name="b09_username_ascii_pattern",
            ),
        ]


class PlayerRating(models.Model):
    """One materialized rating and competitive record per player/game/season/kind."""

    class Kind(models.TextChoices):
        TOURNAMENT = "tournament", "Tournament"
        CHALLENGE = "challenge", "Challenge"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="competitive_ratings"
    )
    game = models.ForeignKey("games.Game", on_delete=models.PROTECT)
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    rating = models.PositiveIntegerField(default=1000)
    played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    last_finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game", "season", "kind"], name="b09_player_rating_scope"
            ),
            models.CheckConstraint(
                condition=Q(played=F("wins") + F("losses") + F("draws")),
                name="b09_rating_record_sum",
            ),
        ]
        indexes = [
            models.Index(
                fields=["game", "season", "kind", "-rating", "user"],
                name="b09_leaderboard_idx",
            ),
        ]


class AppliedMatchEvent(models.Model):
    """Durable unique B08 outbox consumption receipt and head-to-head truth."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_event_id = models.UUIDField(unique=True)
    source_match_id = models.UUIDField(unique=True)
    source_digest = models.CharField(max_length=64)
    game = models.ForeignKey("games.Game", on_delete=models.PROTECT)
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=PlayerRating.Kind.choices)
    source_id = models.CharField(max_length=128)
    competition_title = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rating_events_a"
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rating_events_b"
    )
    score_a = models.PositiveIntegerField()
    score_b = models.PositiveIntegerField()
    rating_a_before = models.PositiveIntegerField()
    rating_b_before = models.PositiveIntegerField()
    rating_a_after = models.PositiveIntegerField()
    rating_b_after = models.PositiveIntegerField()
    finalized_at = models.DateTimeField()
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(user_a=F("user_b")), name="b09_event_distinct_players"
            ),
        ]
        indexes = [
            models.Index(fields=["user_a", "-finalized_at"], name="b09_event_a_recent_idx"),
            models.Index(fields=["user_b", "-finalized_at"], name="b09_event_b_recent_idx"),
            models.Index(
                fields=["game", "season", "kind", "-finalized_at"],
                name="b09_event_scope_recent_idx",
            ),
        ]
