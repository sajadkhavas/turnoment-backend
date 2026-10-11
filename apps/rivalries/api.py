import math
import uuid
from collections import defaultdict
from datetime import datetime

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rankings.models import AppliedMatchEvent

PAGE_SIZE = 20


def gamer_tag(user):
    profile = getattr(user, "player_profile", None)
    if profile and profile.gamer_tag:
        return profile.gamer_tag
    return f"Player-{str(user.pk)[:8]}"


def projection(user):
    events = AppliedMatchEvent.objects.filter(
        Q(user_a=user) | Q(user_b=user),
        user_a__is_active=True, user_b__is_active=True,
    ).select_related(
        "game", "user_a__player_profile", "user_b__player_profile",
    ).order_by("-finalized_at", "source_match_id")
    groups = defaultdict(list)
    for event in events:
        opponent = event.user_b if event.user_a_id == user.pk else event.user_a
        groups[(opponent.pk, event.game_id)].append((event, opponent))
    rows = []
    for (opponent_id, game_id), games in groups.items():
        latest, opponent = games[0]
        own_a = latest.user_a_id == user.pk
        score = latest.score_a if own_a else latest.score_b
        other = latest.score_b if own_a else latest.score_a
        wins = losses = draws = 0
        for event, _ in games:
            side_a = event.user_a_id == user.pk
            ours = event.score_a if side_a else event.score_b
            theirs = event.score_b if side_a else event.score_a
            if ours > theirs:
                wins += 1
            elif ours < theirs:
                losses += 1
            else:
                draws += 1
        edge = "player-leading" if wins > losses else (
            "opponent-leading" if losses > wins else "tied"
        )
        rivalry_id = uuid.uuid5(
            uuid.NAMESPACE_URL, f"turnoment-rivalry:{user.pk}:{opponent_id}:{game_id}"
        )
        rows.append({
            "rivalryId": str(rivalry_id),
            "opponent": {
                "participantId": str(opponent_id), "kind": "player",
                "displayTag": gamer_tag(opponent),
            },
            "game": {
                "gameId": game_id, "name": latest.game.name[:160],
            },
            "headToHead": {
                "totalFinalized": len(games), "playerWins": wins,
                "opponentWins": losses, "draws": draws, "edge": edge,
            },
            "lastEncounter": {
                "matchId": str(latest.source_match_id),
                "finalizedAt": latest.finalized_at.isoformat(),
                "timezone": latest.timezone,
                "playerScore": score, "opponentScore": other,
                "outcome": "win" if score > other else (
                    "loss" if score < other else "draw"
                ),
                "competition": {
                    "kind": latest.kind, "competitionId": latest.source_id,
                    "title": latest.competition_title[:160],
                },
            },
        })
    return rows


class MyRivalriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params
        kind = q.get("kind", "all")
        sort = q.get("sort", "recent")
        game_id = q.get("game")
        try:
            page = int(q.get("page", "1"))
        except (TypeError, ValueError):
            page = 0
        if (
            kind not in ("all", "player", "team")
            or sort not in ("recent", "most-played")
            or not 1 <= page <= 100000
        ):
            return Response({"detail": "Invalid rivalry filters"}, status=400)
        if game_id is not None and (
            not 1 <= len(game_id) <= 128
            or not all(c.isascii() and (c.isalnum() or c in "_-") for c in game_id)
        ):
            return Response({"detail": "Invalid game ID"}, status=400)
        rows = projection(request.user)
        edges = [row["headToHead"]["edge"] for row in rows]
        summary = {
            "totalRivalries": len(rows),
            "totalFinalizedMatches": sum(x["headToHead"]["totalFinalized"] for x in rows),
            "playerLeading": edges.count("player-leading"),
            "tied": edges.count("tied"),
            "opponentLeading": edges.count("opponent-leading"),
        }
        games = sorted(
            {x["game"]["gameId"]: x["game"] for x in rows}.values(),
            key=lambda item: (item["name"], item["gameId"]),
        )
        if kind == "team":
            rows = []
        if game_id is not None:
            rows = [x for x in rows if x["game"]["gameId"] == game_id]
        if sort == "most-played":
            rows.sort(key=lambda x: (
                -x["headToHead"]["totalFinalized"],
                -datetime.fromisoformat(
                    x["lastEncounter"]["finalizedAt"]
                ).timestamp(),
                x["rivalryId"],
            ))
        else:
            rows.sort(key=lambda x: (
                -__import__("datetime").datetime.fromisoformat(
                    x["lastEncounter"]["finalizedAt"]
                ).timestamp(),
                x["rivalryId"],
            ))
        total = len(rows)
        pages = max(1, math.ceil(total / PAGE_SIZE))
        if page > pages:
            return Response({"detail": "Page out of range"}, status=404)
        start = (page - 1) * PAGE_SIZE
        return Response({
            "player": {
                "playerId": str(request.user.pk),
                "gamerTag": gamer_tag(request.user),
            },
            "summary": summary, "games": games,
            "items": rows[start:start + PAGE_SIZE],
            "pagination": {
                "currentPage": page, "totalPages": pages, "totalItems": total,
            },
        })
