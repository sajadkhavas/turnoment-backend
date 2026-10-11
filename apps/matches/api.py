from math import ceil

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .projections import current_player, match_item, visible_matches

PAGE_SIZE = 20


class MyMatchesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = request.query_params.get("state", "all")
        kind = request.query_params.get("kind", "all")
        game_id = request.query_params.get("game")
        page = request.query_params.get("page", "1")
        if state not in {"all", "upcoming", "action-required", "completed", "disputed"}:
            return Response({"detail": "Invalid state filter"}, status=400)
        if kind not in {"all", "tournament", "challenge"}:
            return Response({"detail": "Invalid source filter"}, status=400)
        try:
            number = int(page)
            if number <= 0 or number > 100000:
                raise ValueError()
        except (TypeError, ValueError):
            return Response({"detail": "Invalid page"}, status=400)

        items = [match_item(m, request.user) for m in visible_matches(request.user)]
        summary = {
            "total": len(items),
            "upcoming": sum(x["lifecycleState"] in {"scheduled", "ready", "live"} for x in items),
            "actionRequired": sum(x["attention"] != "none" for x in items),
            "completed": sum(x["lifecycleState"] in {"completed", "cancelled"} for x in items),
            "disputed": sum(x["disputeState"] in {"open", "under-review"} for x in items),
        }
        games = sorted(
            {x["game"]["gameId"]: x["game"] for x in items}.values(),
            key=lambda x: x["name"],
        )
        if state == "upcoming":
            items = [x for x in items if x["lifecycleState"] in {"scheduled", "ready", "live"}]
        elif state == "action-required":
            items = [x for x in items if x["attention"] != "none"]
        elif state == "completed":
            items = [x for x in items if x["lifecycleState"] in {"completed", "cancelled"}]
        elif state == "disputed":
            items = [x for x in items if x["disputeState"] in {"open", "under-review"}]
        if kind != "all":
            items = [x for x in items if x["competition"]["kind"] == kind]
        if game_id:
            items = [x for x in items if x["game"]["gameId"] == game_id]
        total = len(items)
        pages = max(1, ceil(total / PAGE_SIZE))
        number = min(number, pages)
        return Response({
            "player": current_player(request.user),
            "summary": summary,
            "games": games,
            "items": items[(number - 1) * PAGE_SIZE:number * PAGE_SIZE],
            "pagination": {"currentPage": number, "totalPages": pages, "totalItems": total},
        })
