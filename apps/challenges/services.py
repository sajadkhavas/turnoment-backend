"""Synchronous, transactional challenge state changes."""

import hashlib
import json
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from . import integrations
from .models import Challenge, ChallengeCommandReceipt

REQUIRED_FINALIZED_MATCHES = 30
NOTE_MAX_LENGTH = 240
OPPONENT_SEARCH_MIN_CHARS = 2
INVITATION_TTL = timedelta(hours=24)


def fingerprint(command: str, data: dict) -> str:
    raw = json.dumps(
        {"command": command, "data": data},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def receipt_or_none(actor, key, digest):
    old = ChallengeCommandReceipt.objects.filter(actor=actor, key=key).first()
    if old:
        if old.fingerprint != digest:
            return {"outcome": "conflict", "message": "Idempotency key was reused."}
        return old.response
    return None


def remember(actor, key, digest, result):
    ChallengeCommandReceipt.objects.create(
        actor=actor, key=key, fingerprint=digest, response=result
    )
    return result


def access(user):
    stats = integrations.player_challenge_stats(user)
    count = max(0, stats.finalized_valid_matches)
    games = integrations.creation_games(user)
    unlocked = count >= REQUIRED_FINALIZED_MATCHES
    return {
        "unlocked": unlocked,
        "canCreate": bool(
            unlocked and games and user.is_active and integrations.match_creator_ready()
        ),
        "challengeRating": stats.challenge_rating,
        "finalizedValidMatches": count,
        "requiredFinalizedMatches": REQUIRED_FINALIZED_MATCHES,
    }


def expire_pending(challenge, now):
    if challenge.state == Challenge.State.PENDING and challenge.expires_at <= now:
        challenge.state = Challenge.State.EXPIRED
        challenge.revision = uuid.uuid4()
        challenge.save(update_fields=["state", "revision", "updated_at"])
        return True
    return False


def create_challenge(actor, key, payload):
    digest = fingerprint("create", payload)
    pair = sorted((str(actor.pk), str(payload["opponentPlayerId"])))
    with transaction.atomic():
        # Locks two user rows in deterministic order for cross-direction races.
        users = list(
            get_user_model().objects.select_for_update()
            .filter(pk__in=pair).order_by("pk")
        )
        previous = receipt_or_none(actor, key, digest)
        if previous is not None:
            return previous
        if len(users) != 2 or pair[0] == pair[1] or not all(u.is_active for u in users):
            return {"outcome": "validation_error", "fields": {
                "opponent": "Select another eligible player."
            }}
        if not access(actor)["canCreate"]:
            return {"outcome": "unavailable", "message": "Challenge access unavailable."}
        opponent = next((u for u in users if u.pk != actor.pk), None)
        game = next(
            (g for g in integrations.creation_games(actor) if g.game_id == payload["gameId"]),
            None,
        )
        if game is None:
            return {"outcome": "validation_error", "fields": {"game": "Invalid game."}}
        match_format = next(
            (f for f in game.formats if f.format_id == payload["formatId"]), None
        )
        if match_format is None:
            return {"outcome": "validation_error", "fields": {"format": "Invalid format."}}
        if opponent is None or not integrations.opponent_eligible(
            actor, opponent, payload["gameId"]
        ):
            return {"outcome": "unavailable", "message": "Opponent is not eligible."}
        now = timezone.now()
        for old in Challenge.objects.select_for_update().filter(
            pair_low=pair[0], pair_high=pair[1],
            game_id=game.game_id, state=Challenge.State.PENDING,
            expires_at__lte=now,
        ):
            expire_pending(old, now)
        if Challenge.objects.filter(
            pair_low=pair[0], pair_high=pair[1], game_id=game.game_id,
            state__in=[Challenge.State.PENDING, Challenge.State.ACCEPTED],
        ).exists():
            return {"outcome": "conflict", "message": "Active challenge already exists."}
        challenge = Challenge.objects.create(
            challenger=actor, opponent=opponent, pair_low=pair[0], pair_high=pair[1],
            game_id=game.game_id, game_name=game.name,
            format_id=match_format.format_id, format_label=match_format.label,
            note=payload.get("note", "").strip(),
            expires_at=now + INVITATION_TTL,
        )
        result = {
            "outcome": "accepted", "challengeId": str(challenge.pk),
            "revision": str(challenge.revision),
        }
        return remember(actor, key, digest, result)


def mutate_challenge(actor, challenge_id, key, command, payload):
    digest = fingerprint(command, {"challengeId": str(challenge_id), **payload})
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=actor.pk)
        previous = receipt_or_none(actor, key, digest)
        if previous is not None:
            return previous
        challenge = (
            Challenge.objects.select_for_update()
            .filter(Q(challenger=actor) | Q(opponent=actor), pk=challenge_id).first()
        )
        if challenge is None:
            return {"outcome": "unavailable", "message": "Challenge is unavailable."}
        if command == "cancel" and challenge.challenger_id != actor.pk:
            return {"outcome": "unavailable", "message": "Challenge is unavailable."}
        if command in {"accept", "decline"} and challenge.opponent_id != actor.pk:
            return {"outcome": "unavailable", "message": "Challenge is unavailable."}
        if expire_pending(challenge, timezone.now()):
            return {"outcome": "unavailable", "message": "Invitation expired."}
        if str(challenge.revision) != payload["revision"]:
            return {"outcome": "stale", "message": "Challenge revision changed."}
        if challenge.state != Challenge.State.PENDING:
            return {"outcome": "unavailable", "message": "Invitation no longer pending."}
        if command == "accept":
            match_id = integrations.create_match_for_challenge(challenge)
            if not isinstance(match_id, str) or not 1 <= len(match_id) <= 128:
                raise integrations.MatchServiceUnavailable("Invalid B08 match ID")
            if not all(c.isalnum() or c in "_-" for c in match_id):
                raise integrations.MatchServiceUnavailable("Unsafe B08 match ID")
            challenge.match_id = match_id
            challenge.state = Challenge.State.ACCEPTED
        elif command == "decline":
            challenge.state = Challenge.State.DECLINED
        else:
            challenge.state = Challenge.State.CANCELLED
        challenge.revision = uuid.uuid4()
        challenge.save(update_fields=["state", "revision", "match_id", "updated_at"])
        result = {
            "outcome": "accepted", "challengeId": str(challenge.pk),
            "revision": str(challenge.revision),
        }
        return remember(actor, key, digest, result)


def record_finalized_match(challenge_id, match_id, *, challenger_outcome,
                           score_label, challenger_rating_delta=None,
                           opponent_rating_delta=None, completed_at=None):
    """Called by B08 after authoritative result finalization, idempotent by Match."""
    if challenger_outcome not in Challenge.Outcome.values:
        raise ValueError("Invalid match outcome")
    if not score_label or len(score_label) > 80:
        raise ValueError("Final result requires score label")
    completed_at = completed_at or timezone.now()
    with transaction.atomic():
        challenge = Challenge.objects.select_for_update().get(pk=challenge_id)
        same = (
            challenge.match_id == match_id
            and challenge.final_outcome == challenger_outcome
            and challenge.score_label == score_label
            and challenge.challenger_rating_delta == challenger_rating_delta
            and challenge.opponent_rating_delta == opponent_rating_delta
        )
        if challenge.state == Challenge.State.COMPLETED:
            if not same:
                raise ValueError("Conflicting match finalization replay")
            return challenge
        if challenge.state != Challenge.State.ACCEPTED or challenge.match_id != match_id:
            raise ValueError("Challenge not bound to accepted Match")
        challenge.state = Challenge.State.COMPLETED
        challenge.final_outcome = challenger_outcome
        challenge.score_label = score_label
        challenge.completed_at = completed_at
        challenge.challenger_rating_delta = challenger_rating_delta
        challenge.opponent_rating_delta = opponent_rating_delta
        challenge.revision = uuid.uuid4()
        challenge.save()
        return challenge
