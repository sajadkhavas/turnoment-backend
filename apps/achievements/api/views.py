import math
import re
from zoneinfo import ZoneInfo

from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.teams.projections import player_label

from ..models import AchievementDefinition, AchievementProgress

PAGE_SIZE = 12
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def parse_query(params):
    allowed = {"status", "category", "sort", "page"}
    if set(params) - allowed or any(len(params.getlist(k)) != 1 for k in params):
        raise ValidationError({"query": ["Unknown or duplicate query parameter."]})
    status = params.get("status", "all")
    category = params.get("category")
    sort = params.get("sort", "default")
    page = params.get("page", "1")
    if status not in ("all", "locked", "in-progress", "unlocked"):
        raise ValidationError({"status": ["Invalid status."]})
    if sort not in ("default", "recent", "progress"):
        raise ValidationError({"sort": ["Invalid sort mode."]})
    if category is not None and not ID_PATTERN.fullmatch(category):
        raise ValidationError({"category": ["Invalid category identifier."]})
    if not re.fullmatch(r"[0-9]{1,8}", page) or int(page) < 1:
        raise ValidationError({"page": ["Must be positive integer."]})
    return status, category, sort, int(page)


class MyAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status, category, sort, page = parse_query(request.query_params)
        definitions = list(
            AchievementDefinition.objects.filter(is_published=True)
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "player_progress",
                    queryset=AchievementProgress.objects.filter(user=request.user),
                    to_attr="mine",
                )
            )
            .order_by("position", "code")
        )
        categories = {}
        items = []
        for definition in definitions:
            cat = {
                "categoryId": definition.category_id,
                "name": definition.category.name,
            }
            categories[definition.category_id] = cat
            mine = definition.mine[0] if definition.mine else None
            current = min(mine.current, definition.target) if mine else 0
            unlocked = bool(mine and mine.unlocked_at)
            item_status = (
                "unlocked" if unlocked else "in-progress" if current > 0 else "locked"
            )
            percent = min(100, (current * 100) // definition.target)
            if item_status == "in-progress":
                percent = max(1, min(99, percent))
            progress = (
                {"current": current, "target": definition.target, "percent": percent}
                if definition.has_progress else None
            )
            items.append({
                "achievementId": str(definition.pk),
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "category": cat,
                "status": item_status,
                "progress": progress,
                "unlockedAt": mine.unlocked_at.isoformat() if unlocked else None,
            })

        summary = {
            "total": len(items),
            "unlocked": sum(x["status"] == "unlocked" for x in items),
            "inProgress": sum(x["status"] == "in-progress" for x in items),
            "locked": sum(x["status"] == "locked" for x in items),
        }
        selected = [
            item for item in items
            if (status == "all" or item["status"] == status)
            and (category is None or item["category"]["categoryId"] == category)
        ]
        if sort == "recent":
            selected.sort(key=lambda x: (x["unlockedAt"] or "", x["achievementId"]),
                          reverse=True)
        elif sort == "progress":
            selected.sort(key=lambda x: (
                x["progress"]["percent"] if x["progress"] else (
                    100 if x["status"] == "unlocked" else 0
                ), x["achievementId"]
            ), reverse=True)
        pages = max(1, math.ceil(len(selected) / PAGE_SIZE))
        page = min(page, pages)
        return Response({
            "player": {
                "playerId": str(request.user.pk), "gamerTag": player_label(request.user)
            },
            "timezone": ZoneInfo("Asia/Tehran").key,
            "summary": summary,
            "categories": sorted(categories.values(), key=lambda x: x["categoryId"]),
            "items": selected[(page - 1) * PAGE_SIZE:page * PAGE_SIZE],
            "pagination": {
                "currentPage": page, "totalPages": pages, "totalItems": len(selected)
            },
        })
