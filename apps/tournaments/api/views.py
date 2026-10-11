import math
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkins.models import CheckIn
from apps.checkins.services import check_in
from apps.registrations.models import Registration
from apps.registrations.services import register
from apps.tournaments.models import Tournament
from apps.tournaments.projections import context, detail, discovery
from apps.tournaments.services import availability


class DiscoveryQuery(serializers.Serializer):
    game = serializers.RegexField(r"^[A-Za-z0-9_-]{1,128}$", required=False)
    city = serializers.RegexField(r"^[A-Za-z0-9_-]{1,128}$", required=False)
    date = serializers.ChoiceField(
        choices=["today", "tomorrow", "weekend", "week"], required=False
    )
    status = serializers.ChoiceField(
        choices=["open", "filling", "closed", "upcoming"], required=False
    )
    format = serializers.ChoiceField(
        choices=["1v1", "team", "single-elim", "double-elim", "round-robin"],
        required=False
    )
    price = serializers.ChoiceField(
        choices=["free", "lt300", "300-500", "gt500"], required=False
    )
    verified = serializers.BooleanField(required=False, default=False)
    sort = serializers.ChoiceField(
        choices=["suggested", "soonest", "limited", "cheapest", "prize"],
        required=False, default="suggested"
    )
    page = serializers.IntegerField(required=False, min_value=1, max_value=10000, default=1)


class RegisterBody(serializers.Serializer):
    detailVersion = serializers.CharField(max_length=100)
    rulesVersion = serializers.CharField(max_length=60)
    acceptedRules = serializers.BooleanField()
    teamId = serializers.CharField(max_length=128, allow_null=True)


def _tournament(identifier):
    try:
        identifier_id = uuid.UUID(identifier)
    except (ValueError, TypeError):
        return get_object_or_404(Tournament, slug=identifier)
    return get_object_or_404(Tournament, pk=identifier_id)


def _error_fields(errors):
    result = {}
    for key, value in errors.items():
        result[key] = str(value[0]) if isinstance(value, list) else str(value)
    return {"outcome": "validation_error", "fields": result}


class TournamentDiscoveryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = DiscoveryQuery(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(discovery(serializer.validated_data))


class TournamentDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, identifier):
        return Response(detail(_tournament(identifier)))


class TournamentRegistrationContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, identifier):
        return Response(context(_tournament(identifier), request.user))


class TournamentRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, identifier):
        serializer = RegisterBody(data=request.data)
        if not serializer.is_valid():
            return Response(_error_fields(serializer.errors), status=400)
        tournament = _tournament(identifier)
        return Response(register(
            identifier=str(tournament.id), user=request.user,
            payload=serializer.validated_data
        ))


class TournamentCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, identifier):
        tournament = _tournament(identifier)
        registration = Registration.objects.filter(
            user=request.user, tournament=tournament, status="confirmed"
        ).first()
        if registration is None:
            return Response({"outcome": "unavailable", "reason": "not_registered"})
        record = CheckIn.objects.filter(registration=registration).first()
        if record is not None:
            return Response({"outcome": "completed", "checkedAt": record.checked_at.isoformat()})
        return Response({
            "outcome": "open" if availability(tournament) == "closed"
            and tournament.check_in_opens_at else "not_open"
        })

    def post(self, request, identifier):
        return Response(check_in(tournament=_tournament(identifier), user=request.user))


class MyTournamentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = request.query_params.get("state", "all")
        if state not in {"all", "upcoming", "live", "completed"}:
            return Response({"error": {"code": "invalid_state"}}, status=400)
        try:
            page = int(request.query_params.get("page", "1"))
        except (ValueError, TypeError):
            return Response({"error": {"code": "invalid_page"}}, status=400)
        if page < 1 or page > 10000:
            return Response({"error": {"code": "invalid_page"}}, status=400)
        registrations = list(
            Registration.objects.filter(user=request.user, status="confirmed")
            .select_related("tournament").order_by("tournament__starts_at", "id")
        )
        def mapped_state(t):
            if t.lifecycle in {t.Lifecycle.LIVE, t.Lifecycle.CHECK_IN}:
                return "live" if t.lifecycle == t.Lifecycle.LIVE else "upcoming"
            if t.lifecycle == t.Lifecycle.COMPLETED:
                return "completed"
            if t.lifecycle == t.Lifecycle.CANCELLED:
                return "cancelled"
            return "upcoming"

        summary = {
            "total": len(registrations),
            "upcoming": sum(mapped_state(r.tournament) == "upcoming" for r in registrations),
            "live": sum(mapped_state(r.tournament) == "live" for r in registrations),
            "completed": sum(mapped_state(r.tournament) == "completed" for r in registrations),
        }
        games = {
            r.tournament.game_key: {
                "gameId": r.tournament.game_key, "name": r.tournament.game_name
            } for r in registrations
        }
        game_filter = request.query_params.get("game")
        if game_filter:
            registrations = [r for r in registrations if r.tournament.game_key == game_filter]
        if state != "all":
            registrations = [r for r in registrations if mapped_state(r.tournament) == state]
        pages = max(1, math.ceil(len(registrations) / 12))
        page = min(page, pages)
        current = registrations[(page - 1) * 12:page * 12]
        checkins = set(
            CheckIn.objects.filter(registration__in=current)
            .values_list("registration_id", flat=True)
        )
        items = []
        for reg in current:
            t = reg.tournament
            tournament_state = mapped_state(t)
            checked = reg.id in checkins
            from django.utils import timezone

            now = timezone.now()
            if checked:
                ci = "completed"
            elif not t.check_in_opens_at:
                ci = "not-required"
            elif t.check_in_opens_at > now:
                ci = "not-open"
            elif now >= t.starts_at:
                ci = "missed"
            else:
                ci = "open"
            action = (
                "view-results" if tournament_state == "completed" else
                "view-bracket" if tournament_state == "live" else
                "check-in" if ci == "open" else "view"
            )
            participation = (
                {"kind": "individual"} if not reg.team_id else
                {
                    "kind": "team", "teamId": reg.team_id,
                    "teamName": reg.team_name, "role": reg.team_role
                }
            )
            items.append({
                "tournamentId": str(t.id), "tournamentSlug": t.slug,
                "title": t.title,
                "game": {"gameId": t.game_key, "name": t.game_name},
                "venue": {
                    "gamingCenterId": t.center_key, "name": t.center_name,
                    "city": t.center_city
                },
                "startsAt": t.starts_at.isoformat(), "timezone": "Asia/Tehran",
                "formatLabel": t.format_label, "lifecycleState": tournament_state,
                "registrationState": "confirmed", "checkInState": ci,
                "participation": participation, "result": None, "nextAction": action,
            })
        return Response({
            "summary": summary, "games": list(games.values()), "items": items,
            "pagination": {
                "currentPage": page, "totalPages": pages,
                "totalItems": len(registrations)
            },
        })
