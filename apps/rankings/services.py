import hashlib
import json
import math
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.games.models import Game

from .models import AppliedMatchEvent, PlayerRating, Season

INITIAL_RATING = 1000
ELO_K = 32


@dataclass(frozen=True)
class FinalizedInput:
    """Verified B08 record translated into B09's stable internal ingestion schema."""

    event_id: uuid.UUID
    match_id: uuid.UUID
    player_a_id: uuid.UUID
    player_b_id: uuid.UUID
    game_id: str
    kind: str
    source_id: str
    competition_title: str
    timezone: str
    score_a: int
    score_b: int
    finalized_at: datetime


def event_digest(item: FinalizedInput) -> str:
    return hashlib.sha256(
        json.dumps(asdict(item), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def outcome(score, opponent):
    return "win" if score > opponent else "loss" if score < opponent else "draw"


def elo_delta(rating_a, rating_b, score_a, score_b):
    actual = 1 if score_a > score_b else 0 if score_a < score_b else 0.5
    expected = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    return round(ELO_K * (actual - expected))


def _validate(item: FinalizedInput):
    if not isinstance(item, FinalizedInput):
        raise ValidationError("Expected a verified finalization input")
    ids = (item.event_id, item.match_id, item.player_a_id, item.player_b_id)
    if not all(isinstance(value, uuid.UUID) for value in ids):
        raise ValidationError("Invalid immutable event identity")
    if item.player_a_id == item.player_b_id:
        raise ValidationError("Match requires two different players")
    if item.kind not in PlayerRating.Kind.values:
        raise ValidationError("Unsupported ranking type")
    if (
        type(item.score_a) is not int or type(item.score_b) is not int
        or item.score_a < 0 or item.score_b < 0
    ):
        raise ValidationError("Invalid finalized scores")
    if timezone.is_naive(item.finalized_at):
        raise ValidationError("Finalization must be timezone aware")
    if (
        not isinstance(item.source_id, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", item.source_id)
    ):
        raise ValidationError("Invalid stable source identifier")
    if (
        not isinstance(item.game_id, str) or not item.game_id
        or not isinstance(item.source_id, str) or not item.source_id
        or not isinstance(item.competition_title, str) or not item.competition_title
        or not isinstance(item.timezone, str) or not item.timezone
    ):
        raise ValidationError("Missing authoritative match metadata")


@transaction.atomic
def apply_verified_finalization(item: FinalizedInput):
    """Internal trusted-input function. NOT an HTTP endpoint.

    Locks Season before accessing scoped ratings so concurrent consumers serialize
    even when neither PlayerRating row exists yet. PostgreSQL constraints are the
    final defense against duplicate event / match identities.
    """
    _validate(item)
    digest = event_digest(item)
    prior = AppliedMatchEvent.objects.filter(
        Q(source_event_id=item.event_id) | Q(source_match_id=item.match_id)
    ).first()
    if prior:
        if (
            prior.source_event_id != item.event_id
            or prior.source_match_id != item.match_id
            or prior.source_digest != digest
        ):
            raise ValidationError("Conflicting finalized event replay")
        return prior, False

    seasons = list(
        Season.objects.select_for_update().filter(
            starts_at__lte=item.finalized_at, ends_at__gt=item.finalized_at
        )
    )
    if len(seasons) != 1:
        raise ValidationError("Finalization requires exactly one configured season")
    season = seasons[0]

    prior = AppliedMatchEvent.objects.filter(
        Q(source_event_id=item.event_id) | Q(source_match_id=item.match_id)
    ).first()
    if prior:
        if (
            prior.source_event_id != item.event_id
            or prior.source_match_id != item.match_id
            or prior.source_digest != digest
        ):
            raise ValidationError("Conflicting finalized event replay")
        return prior, False

    game = Game.objects.filter(pk=item.game_id).first()
    if game is None:
        raise ValidationError("Unknown authoritative game")
    if AppliedMatchEvent.objects.filter(
        game=game, season=season, kind=item.kind,
        finalized_at__gt=item.finalized_at,
    ).exists():
        raise ValidationError("Out-of-order finalized event: drain chronologically")

    users = sorted([item.player_a_id, item.player_b_id], key=str)
    ratings = {}
    for user_id in users:
        rating, _ = PlayerRating.objects.select_for_update().get_or_create(
            user_id=user_id, game=game, season=season, kind=item.kind,
        )
        ratings[user_id] = rating
    rating_a = ratings[item.player_a_id]
    rating_b = ratings[item.player_b_id]
    before_a, before_b = rating_a.rating, rating_b.rating
    delta = elo_delta(before_a, before_b, item.score_a, item.score_b)
    rating_a.rating = max(0, before_a + delta)
    rating_b.rating = max(0, before_b - delta)
    for rating, score, other in (
        (rating_a, item.score_a, item.score_b),
        (rating_b, item.score_b, item.score_a),
    ):
        rating.played += 1
        result = outcome(score, other)
        if result == "win":
            rating.wins += 1
        elif result == "loss":
            rating.losses += 1
        else:
            rating.draws += 1
        rating.last_finalized_at = item.finalized_at
        rating.save(update_fields=[
            "rating", "played", "wins", "losses", "draws", "last_finalized_at",
        ])

    applied = AppliedMatchEvent.objects.create(
        source_event_id=item.event_id,
        source_match_id=item.match_id,
        source_digest=digest,
        game=game, season=season, kind=item.kind,
        source_id=item.source_id,
        competition_title=item.competition_title,
        timezone=item.timezone,
        user_a_id=item.player_a_id, user_b_id=item.player_b_id,
        score_a=item.score_a, score_b=item.score_b,
        rating_a_before=before_a, rating_b_before=before_b,
        rating_a_after=rating_a.rating, rating_b_after=rating_b.rating,
        finalized_at=item.finalized_at,
    )
    return applied, True


def apply_b08_event(event_id):
    """Only authoritative B08 database events can enter production ranking truth.

    Import deliberately deferred until B08 workstream is integrated by B99.
    """
    from apps.matches.models import Match
    from apps.results.models import FinalizedResultEvent

    source = FinalizedResultEvent.objects.select_related("match").get(pk=event_id)
    match = source.match
    if match.state != Match.State.COMPLETED:
        raise ValidationError("B08 match is not currently finalized")
    if (
        source.player_a_id != match.participant_a_id
        or source.player_b_id != match.participant_b_id
    ):
        raise ValidationError("B08 event/match participant conflict")
    verified = FinalizedInput(
        event_id=source.id, match_id=match.pk,
        player_a_id=source.player_a_id, player_b_id=source.player_b_id,
        game_id=match.game_id, kind=match.source_kind,
        source_id=match.source_id, competition_title=match.competition_title,
        timezone=match.timezone, score_a=source.score_a, score_b=source.score_b,
        finalized_at=source.finalized_at,
    )
    return apply_verified_finalization(verified)


def drain_b08_events(limit=100):
    """B99/Celery/scheduler integration seam; safe repeated invocation."""
    from apps.results.models import FinalizedResultEvent

    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValidationError("Invalid drain limit")
    consumed = 0
    events = FinalizedResultEvent.objects.order_by("finalized_at", "id")
    for source in events.iterator(chunk_size=100):
        if not AppliedMatchEvent.objects.filter(source_event_id=source.pk).exists():
            apply_b08_event(source.pk)
            consumed += 1
            if consumed >= limit:
                break
    return consumed
