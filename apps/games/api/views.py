import re

from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.selectors import (
    catalog_item,
    detail_projection,
    home_game_projection,
    published_games,
    search_games,
)

_MAX_FILTER_LENGTH = 120
_ALLOWED_PARAMS = frozenset({"q", "platform", "slug", "gameId"})


class PublicGameAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


class GameCatalogView(PublicGameAPIView):
    def get(self, request):
        query = request.query_params
        if set(query) - _ALLOWED_PARAMS:
            raise ValidationError({"query": "Unknown filter."})
        if any(len(query.getlist(key)) != 1 for key in query):
            raise ValidationError({"query": "Duplicate filters are not allowed."})
        filters = {}
        for param in _ALLOWED_PARAMS:
            raw = query.get(param, "")
            if len(raw) > _MAX_FILTER_LENGTH or any(
                ord(char) < 32 or ord(char) == 127 for char in raw
            ):
                raise ValidationError({param: "Invalid filter value."})
            value = raw.strip()
                raise ValidationError({param: "Invalid filter value."})
            filters[param] = value
        for key in ("slug", "gameId"):
            pattern = r"[a-z0-9]+(?:-[a-z0-9]+)*" if key == "slug" else r"[A-Za-z0-9_-]{1,128}"
            if filters[key] and not re.fullmatch(pattern, filters[key]):
                raise ValidationError({key: "Invalid identifier."})
        queryset = search_games(
            q=filters["q"], platform=filters["platform"],
            slug=filters["slug"], game_id=filters["gameId"],
        )
        # The v1 frontend schema is explicitly non-paginated, maximum 100.
        games = list(queryset[:101])
        if len(games) > 100:
            return Response({"error": {"code": "catalog_capacity_exceeded"}}, status=503)
        return Response({
            "schemaVersion": 1,
            "totalItems": len(games),
            "items": [catalog_item(game) for game in games],
        })


class GameDetailView(PublicGameAPIView):
    def get(self, request, slug):
        game = published_games().filter(slug=slug).prefetch_related("competitive_formats").first()
        if game is None:
            raise Http404
        return Response(detail_projection(game))


class PublicHomeView(PublicGameAPIView):
    def get(self, request):
        if request.query_params:
            raise ValidationError({"query": "Home discovery does not accept filters."})
        return Response(home_game_projection())
