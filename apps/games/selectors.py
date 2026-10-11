from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Q

from .models import Game


def published_games():
    """Single authority for the public catalog, details and home finder."""
    return Game.objects.filter(publication_state=Game.Publication.PUBLISHED)


def search_games(*, q="", platform="", slug="", game_id=""):
    qs = published_games()
    if q:
        vector = SearchVector("name", "short_name", "description", config="simple")
        qs = qs.annotate(_search=vector).filter(
            Q(_search=SearchQuery(q, config="simple"))
            | Q(name__icontains=q)
            | Q(short_name__icontains=q)
        )
    if platform:
        qs = qs.filter(platforms__contains=[platform])
    if slug:
        qs = qs.filter(slug=slug)
    if game_id:
        qs = qs.filter(id=game_id)
    return qs.order_by("sort_order", "id")


def game_identity(game):
    return {"gameId": game.pk, "slug": game.slug, "name": game.name}


def catalog_item(game):
    return {
        **game_identity(game),
        "publicationState": "published",
        "shortName": game.short_name,
        "description": game.description,
        "platforms": game.platforms,
        "coverImage": game.cover_image,
        # B05 owns authoritative tournament counting; null does not mean zero.
        "tournamentCount": None,
    }


def detail_projection(game, *, related=None):
    """Pure game-owned projection; B04/B05/B09 provide later authoritative related data.

    The empty projection is valid only while no related domain records exist.
    Integration must replace this seam when those modules are installed/populated.
    """
    related = related or {
        "stats": {
            "openTournamentCount": 0,
            "upcomingTournamentCount": 0,
            "supportingCenterCount": 0,
            "rankedPlayerCount": 0,
        },
        "tournaments": [],
        "ranking": {"state": "empty", "entries": []},
        "centers": [],
    }
    return {
        "id": game.pk,
        "slug": game.slug,
        "detailVersion": game.detail_version,
        "publicationState": "published",
        "name": game.name,
        "shortName": game.short_name,
        "description": game.description,
        "heroImage": game.hero_image,
        "platforms": game.platforms,
        "competitiveFormats": [
            {
                "id": item.key, "label": item.label,
                "description": item.description, "teamSize": item.team_size,
            }
            for item in game.competitive_formats.all()
        ],
        **related,
        "seo": {
            "title": game.seo_title or game.name,
            "description": game.seo_description or game.description,
        },
    }


DATE_BUCKETS = (
    {"value": "today", "label": "امروز"},
    {"value": "tomorrow", "label": "فردا"},
    {"value": "weekend", "label": "آخر هفته"},
    {"value": "week", "label": "این هفته"},
)


def home_game_projection():
    """B03's game-owned Home slice, with safe empty slots for other workstreams."""
    return {
        "schemaVersion": 1,
        "finder": {
            "games": [game_identity(game) for game in published_games()[:30]],
            "cities": [],
            "dateBuckets": list(DATE_BUCKETS),
        },
        # Requires B05's authoritative activeTournamentCount; no invented zeros.
        "popularGames": [],
        "featuredTournaments": [],
        "featuredGamingCenters": [],
    }
