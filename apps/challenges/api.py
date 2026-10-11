"""Private F15 Challenge Hub endpoints; no Challenge Detail endpoint."""

import re
from math import ceil

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PlayerProfile

from . import integrations, services
from .models import Challenge

FILTERS = {"all", "incoming", "outgoing", "active", "action-required", "completed"}
PAGE_SIZE = 20
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,200}$")


class ChallengeCreateSerializer(serializers.Serializer):
    opponentPlayerId = serializers.UUIDField()
    gameId = serializers.RegexField(r"^[A-Za-z0-9_-]{1,128}$")
    formatId = serializers.RegexField(r"^[A-Za-z0-9_-]{1,128}$")
    note = serializers.CharField(
        max_length=services.NOTE_MAX_LENGTH, allow_blank=True, required=False, trim_whitespace=True
    )


class ChallengeRespondSerializer(serializers.Serializer):
    revision = serializers.UUIDField()
    action = serializers.ChoiceField(choices=("accept", "decline"))


class ChallengeCancelSerializer(serializers.Serializer):
    revision = serializers.UUIDField()


def player_name(user):
    profile = getattr(user, "player_profile", None)
    name = (profile.gamer_tag or "").strip() if profile else ""
    return name or f"player-{user.pk.hex[:8]}"


def opponent_projection(user, rating=None):
    name = player_name(user)
    return {
        "playerId": str(user.pk), "username": name, "gamerTag": name,
        "avatarInitials": name[:2].upper(),
        "challengeRating": rating,
    }


def lifecycle(challenge, now):
    if challenge.state == Challenge.State.PENDING and challenge.expires_at <= now:
        return "invitation-expired"
    return {
        Challenge.State.PENDING: "invitation-pending",
        Challenge.State.ACCEPTED: "accepted",
        Challenge.State.DECLINED: "invitation-declined",
        Challenge.State.CANCELLED: "cancelled",
        Challenge.State.EXPIRED: "invitation-expired",
        Challenge.State.COMPLETED: "completed",
    }[challenge.state]


def item_projection(challenge, actor, now):
    incoming = challenge.opponent_id == actor.pk
    other = challenge.challenger if incoming else challenge.opponent
    state = lifecycle(challenge, now)
    actions = (
        ["accept", "decline"] if incoming and state == "invitation-pending"
        else ["cancel"] if not incoming and state == "invitation-pending"
        else []
    )
    labels = {
        "invitation-pending": "در انتظار پاسخ تو" if incoming else "منتظر پاسخ حریف",
        "invitation-expired": "مهلت پاسخ تمام شده",
        "invitation-declined": "دعوت رد شده",
        "accepted": "پذیرفته‌شده",
        "completed": "پایان‌یافته",
        "cancelled": "لغوشده",
    }
    match = (
        {
            "matchId": challenge.match_id, "startsAtLabel": None,
            "venueLabel": None, "contextLabel": "حضوری",
        } if challenge.match_id else None
    )
    result = None
    if state == "completed":
        outcome = challenge.final_outcome
        if incoming:
            outcome = {"win": "loss", "loss": "win"}.get(outcome, outcome)
        result = {
            "outcome": outcome, "scoreLabel": challenge.score_label,
            "ratingDelta": (
                challenge.opponent_rating_delta if incoming
                else challenge.challenger_rating_delta
            ),
            "completedAtLabel": timezone.localtime(challenge.completed_at).strftime(
                "%Y-%m-%d %H:%M"
            ),
        }
    return {
        "challengeId": str(challenge.pk), "revision": str(challenge.revision),
        "direction": "incoming" if incoming else "outgoing",
        "lifecycle": state, "statusLabel": labels[state],
        "actionRequiredLabel": (
            "این دعوت منتظر پاسخ توست." if incoming and actions else None
        ),
        "opponent": opponent_projection(other),
        "game": {"gameId": challenge.game_id, "name": challenge.game_name},
        "format": {"formatId": challenge.format_id, "label": challenge.format_label},
        "createdAtLabel": timezone.localtime(challenge.created_at).strftime(
            "%Y-%m-%d %H:%M"
        ),
        "responseDeadlineLabel": (
            timezone.localtime(challenge.expires_at).strftime("%Y-%m-%d %H:%M")
            if state == "invitation-pending" else None
        ),
        "note": challenge.note or None,
        "match": match, "result": result, "allowedCommands": actions,
        "navigationTarget": (
            {"kind": "my-matches"} if match is not None else None
        ),
    }


def group(challenge, actor, now):
    state = lifecycle(challenge, now)
    if state == "invitation-pending":
        return "incoming" if challenge.opponent_id == actor.pk else "outgoing"
    if state == "accepted":
        return "active"
    return "completed"


def action_response(payload):
    outcomes = {
        "accepted": status.HTTP_200_OK, "validation_error": status.HTTP_400_BAD_REQUEST,
        "conflict": status.HTTP_409_CONFLICT, "stale": status.HTTP_409_CONFLICT,
        "unavailable": status.HTTP_404_NOT_FOUND,
    }
    return Response(payload, status=outcomes[payload["outcome"]])


def validate_command(request, serializer_class, allowed):
    if not isinstance(request.data, dict) or set(request.data) - allowed:
        return None, Response(
            {"outcome": "validation_error", "fields": {
                "form": "Request contains unsupported fields."
            }}, status=status.HTTP_400_BAD_REQUEST
        )
    parsed = serializer_class(data=request.data)
    if not parsed.is_valid():
        fields = {
            {"opponentPlayerId": "opponent", "gameId": "game", "formatId": "format"}
            .get(k, k): str(v[0]) for k, v in parsed.errors.items()
        }
        return None, Response(
            {"outcome": "validation_error", "fields": fields},
            status=status.HTTP_400_BAD_REQUEST,
        )
    key = request.headers.get("Idempotency-Key", "")
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        return None, Response(
            {"outcome": "validation_error", "fields": {
                "form": "A valid Idempotency-Key header is required."
            }}, status=status.HTTP_400_BAD_REQUEST,
        )
    return (parsed.validated_data, key), None


class PrivateChallengeView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


class ChallengeHubView(PrivateChallengeView):
    def get(self, request):
        state_filter = request.query_params.get("status", "all")
        page_raw = request.query_params.get("page", "1")
        if state_filter not in FILTERS or not page_raw.isascii() or not page_raw.isdecimal():
            return Response({"detail": "Invalid status or page."}, status=400)
        page = int(page_raw)
        if not 1 <= page <= 1000000:
            return Response({"detail": "Invalid page."}, status=400)
        # Use database aggregation and bounded pagination; safe GET never writes.
        now = timezone.now()
        actor_scope = Q(challenger=request.user) | Q(opponent=request.user)
        pending = Q(state=Challenge.State.PENDING, expires_at__gt=now)
        incoming = pending & Q(opponent=request.user)
        outgoing = pending & Q(challenger=request.user)
        active = Q(state=Challenge.State.ACCEPTED)
        completed = (
            ~Q(state__in=[Challenge.State.PENDING, Challenge.State.ACCEPTED])
            | Q(state=Challenge.State.PENDING, expires_at__lte=now)
        )
        scoped = Challenge.objects.filter(actor_scope)
        summary = {
            "incoming": scoped.filter(incoming).count(),
            "outgoing": scoped.filter(outgoing).count(),
            "active": scoped.filter(active).count(),
            "completed": scoped.filter(completed).count(),
        }
        query = scoped
        if state_filter in {"incoming", "action-required"}:
            query = query.filter(incoming)
        elif state_filter == "outgoing":
            query = query.filter(outgoing)
        elif state_filter == "active":
            query = query.filter(active)
        elif state_filter == "completed":
            query = query.filter(completed)
        total = query.count()
        pages = ceil(total / PAGE_SIZE)
        current = min(page, pages) if pages else 1
        first = (current - 1) * PAGE_SIZE
        selected = list(
            query.select_related(
                "challenger__player_profile", "opponent__player_profile"
            ).order_by("-created_at", "-pk")[first:first + PAGE_SIZE]
        )
        games = integrations.creation_games(request.user)
        return Response({
            "player": {
                "playerId": str(request.user.pk),
                "username": player_name(request.user),
                "gamerTag": player_name(request.user),
            },
            "access": services.access(request.user),
            "creation": {
                "games": [
                    {
                        "gameId": g.game_id, "name": g.name,
                        "formats": [
                            {"formatId": f.format_id, "label": f.label}
                            for f in g.formats
                        ],
                    } for g in games
                ],
                "opponentSearchMinChars": services.OPPONENT_SEARCH_MIN_CHARS,
                "noteMaxLength": services.NOTE_MAX_LENGTH,
            },
            "summary": summary,
            "items": [
                item_projection(ch, request.user, now)
                for ch in selected
            ],
            "pagination": {
                "currentPage": current, "totalPages": pages, "totalItems": total,
            },
        })

    def post(self, request):
        command, error = validate_command(
            request, ChallengeCreateSerializer,
            {"opponentPlayerId", "gameId", "formatId", "note"},
        )
        if error:
            return error
        data, key = command
        payload = {
            "opponentPlayerId": str(data["opponentPlayerId"]),
            "gameId": data["gameId"], "formatId": data["formatId"],
            "note": data.get("note", ""),
        }
        return action_response(services.create_challenge(request.user, key, payload))


class OpponentSearchView(PrivateChallengeView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        game_id = request.query_params.get("game", "")
        if not services.OPPONENT_SEARCH_MIN_CHARS <= len(query) <= 80:
            return Response({
                "outcome": "validation_error", "message": "Search requires 2 to 80 characters."
            }, status=400)
        valid_game = any(
            g.game_id == game_id for g in integrations.creation_games(request.user)
        )
        if not valid_game:
            return Response({
                "outcome": "validation_error", "message": "Invalid game."
            }, status=400)
        if not services.access(request.user)["canCreate"]:
            return Response({"outcome": "results", "query": query, "items": []})
        profiles = (
            PlayerProfile.objects.select_related("user")
            .filter(gamer_tag__icontains=query, user__is_active=True)
            .exclude(user=request.user).order_by("gamer_tag")[:100]
        )
        opponents = [
            opponent_projection(profile.user)
            for profile in profiles
            if integrations.opponent_eligible(request.user, profile.user, game_id)
        ][:20]
        return Response({"outcome": "results", "query": query, "items": opponents})


class ChallengeResponseView(PrivateChallengeView):
    def post(self, request, challenge_id):
        command, error = validate_command(
            request, ChallengeRespondSerializer, {"revision", "action"}
        )
        if error:
            return error
        data, key = command
        try:
            result = services.mutate_challenge(
                request.user, challenge_id, key, data["action"],
                {"revision": str(data["revision"])},
            )
        except integrations.MatchServiceUnavailable:
            return Response({
                "outcome": "unavailable", "message": "Match service is unavailable."
            }, status=503)
        return action_response(result)


class ChallengeCancelView(PrivateChallengeView):
    def post(self, request, challenge_id):
        command, error = validate_command(
            request, ChallengeCancelSerializer, {"revision"}
        )
        if error:
            return error
        data, key = command
        return action_response(services.mutate_challenge(
            request.user, challenge_id, key, "cancel",
            {"revision": str(data["revision"])},
        ))
