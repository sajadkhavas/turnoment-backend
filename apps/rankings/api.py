import math
import re

from django.db.models import Q
from django.http import Http404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game
from apps.gaming_centers.models import City

from .models import AppliedMatchEvent, PlayerRating, PublicRankingIdentity, Season

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
USERNAME = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
PAGE_SIZE = 20


def public_game(game):
    return {"gameId": game.pk, "slug": game.slug, "name": game.name[:160]}


def public_city(city):
    return {"cityId": str(city.pk), "slug": city.slug, "name": city.name[:160]}


def public_season(season):
    return {"id": str(season.pk), "slug": season.slug, "label": season.label}


def public_ratings(game, season, kind, city=None):
    qs = PlayerRating.objects.select_related(
        "game", "season", "user__player_profile",
        "user__ranking_identity__city",
    ).filter(
        game=game, season=season, kind=kind,
        user__is_active=True,
        user__ranking_identity__is_published=True,
        user__player_profile__gamer_tag__isnull=False,
    ).exclude(user__player_profile__gamer_tag="")
    if city:
        qs = qs.filter(user__ranking_identity__city=city)
    # Rank is assigned after applying ALL filters and before pagination.
    return qs.order_by("-rating", "-wins", "-played", "user_id")


def flat_movement():
    # No prior published rank snapshot exists; v1 exposes stable neutral movement.
    return {"direction": "flat", "positions": 0}


def ranking_row(row, position):
    identity = row.user.ranking_identity
    return {
        "playerId": str(row.user_id), "username": identity.username,
        "gamerTag": row.user.player_profile.gamer_tag,
        "city": public_city(identity.city),
        "game": public_game(row.game), "rank": position,
        "rating": row.rating, "ratingType": row.kind,
        "played": row.played, "wins": row.wins,
        "losses": row.losses, "draws": row.draws,
        "movement": flat_movement(),
    }


def ranking_filters():
    games = list(Game.objects.filter(publication_state="published").order_by("slug"))
    seasons = list(Season.objects.filter(is_published=True).order_by("-starts_at", "slug"))
    regions = list(City.objects.filter(
        ranking_identities__is_published=True,
        ranking_identities__user__is_active=True,
    ).distinct().order_by("slug"))
    return games, seasons, regions


class PublicRankingView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params
        allowed = {"game", "season", "region", "type", "page"}
        if set(q) - allowed or any(len(q.getlist(k)) != 1 for k in q):
            return Response({"detail": "Unknown or duplicate filter"}, status=400)
        kind = q.get("type", "tournament")
        if kind not in PlayerRating.Kind.values:
            return Response({"detail": "Invalid rating type"}, status=400)
        try:
            page = int(q.get("page", "1"))
        except (TypeError, ValueError):
            page = 0
        if not 1 <= page <= 100000:
            return Response({"detail": "Invalid page"}, status=400)
        for field in ("game", "season", "region"):
            if field in q and not SLUG.fullmatch(q[field]):
                return Response({"detail": f"Invalid {field}"}, status=400)
        games, seasons, regions = ranking_filters()
        if not games or not seasons:
            return Response({"detail": "No published ranking game or season"}, status=503)
        game_slug = q.get("game", games[0].slug)
        season_slug = q.get("season", seasons[0].slug)
        game = next((g for g in games if g.slug == game_slug), None)
        season = next((s for s in seasons if s.slug == season_slug), None)
        region_slug = q.get("region")
        region = next((r for r in regions if r.slug == region_slug), None)
        if game is None or season is None or (region_slug and region is None):
            return Response({"detail": "Unknown ranking filter"}, status=400)
        rows = public_ratings(game, season, kind, region)
        count = rows.count()
        pages = max(1, math.ceil(count / PAGE_SIZE))
        if page > pages:
            return Response({"detail": "Page out of range"}, status=404)
        start = (page - 1) * PAGE_SIZE
        page_rows = list(rows[start:start + PAGE_SIZE])
        return Response({
            "schemaVersion": 1,
            "filters": {
                "games": [public_game(g) for g in games[:100]],
                "seasons": [public_season(s) for s in seasons[:50]],
                "regions": [
                    {"id": str(c.pk), "slug": c.slug, "label": c.name[:160]}
                    for c in regions[:100]
                ],
                "types": [
                    {"id": "tournament", "label": "Tournament"},
                    {"id": "challenge", "label": "Challenge"},
                ],
            },
            "activeQuery": {
                "game": game.slug, "season": season.slug,
                **({"region": region.slug} if region else {}),
                "type": kind, "page": page,
            },
            "items": [
                ranking_row(row, start + number + 1)
                for number, row in enumerate(page_rows)
            ],
            "pagination": {
                "currentPage": page, "totalPages": pages,
                "totalItems": count, "pageSize": PAGE_SIZE,
            },
        })


def profile_snapshots(user):
    rows = list(public_ratings_for_user(user))
    snapshots = []
    for row in rows[:24]:
        visible = list(public_ratings(row.game, row.season, row.kind))
        rank = next(
            (i for i, candidate in enumerate(visible, 1) if candidate.user_id == user.pk),
            None,
        )
        snapshots.append({
            "snapshotId": str(row.pk),
            "game": public_game(row.game),
            "season": {
                "seasonId": str(row.season_id),
                "slug": row.season.slug,
                "label": row.season.label,
            },
            "ratingType": row.kind, "rating": row.rating, "rank": rank,
            "played": row.played, "wins": row.wins,
            "losses": row.losses, "draws": row.draws,
            "movement": flat_movement(),
        })
    return snapshots


def public_ratings_for_user(user):
    return PlayerRating.objects.filter(user=user, season__is_published=True,
        game__publication_state="published").select_related(
        "game", "season",
    ).order_by("-season__starts_at", "game__slug", "kind")


def profile_recent_results(user):
    events = AppliedMatchEvent.objects.filter(
        Q(user_a=user) | Q(user_b=user), kind="tournament",
        game__publication_state="published",
    ).select_related("game", "user_a__player_profile", "user_b__player_profile")
    items = []
    for event in events.order_by("-finalized_at", "source_match_id")[:50]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", event.source_id):
            continue
        is_a = event.user_a_id == user.pk
        own = event.score_a if is_a else event.score_b
        other = event.score_b if is_a else event.score_a
        opponent = event.user_b if is_a else event.user_a
        peer_identity = PublicRankingIdentity.objects.filter(
            user=opponent, is_published=True, user__is_active=True,
        ).exists()
        opponent_tag = getattr(opponent.player_profile, "gamer_tag",
            None) if peer_identity else None
        items.append({
            "resultId": str(event.source_match_id),
            "tournament": {
                "tournamentId": event.source_id,
                "name": event.competition_title[:160],
            },
            "game": public_game(event.game),
            "outcome": "win" if own > other else "loss" if own < other else "draw",
            "opponentGamerTag": opponent_tag,
            "completedAt": event.finalized_at.isoformat(),
        })
        if len(items) == 10:
            break
    return items


class PublicCompetitiveProfileView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        if not USERNAME.fullmatch(username):
            raise Http404
        identity = PublicRankingIdentity.objects.select_related(
            "user__player_profile", "city"
        ).filter(username=username, is_published=True, user__is_active=True).first()
        if identity is None or not identity.user.player_profile.gamer_tag:
            raise Http404
        return Response({
            "schemaVersion": 1, "publicationState": "published",
            "searchVisibility": identity.search_visibility,
            "playerId": str(identity.user_id),
            "username": identity.username,
            "gamerTag": identity.user.player_profile.gamer_tag,
            "avatarUrl": None,
            "city": public_city(identity.city),
            "publicBio": None,
            "competitiveSnapshots": profile_snapshots(identity.user),
            "recentResults": profile_recent_results(identity.user),
        })
