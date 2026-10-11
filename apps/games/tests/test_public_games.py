from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections
from rest_framework.test import APIClient

from apps.games.models import CompetitiveFormat, Game


def make_game(*, slug="tekken-8", state="published", game_id="tekken8", **kwargs):
    return Game.objects.create(
        id=game_id,
        slug=slug,
        publication_state=state,
        name="Tekken 8",
        short_name="Tekken",
        description="Competitive Tekken eight tournaments and events.",
        platforms=["PS5", "PC"],
        **kwargs,
    )


@pytest.mark.django_db
def test_anonymous_catalog_and_detail_are_strict_and_stable():
    game = make_game()
    CompetitiveFormat.objects.create(
        game=game, key="one-on-one", label="1 versus 1",
        description="One-on-one competitive format", team_size=1,
    )
    client = APIClient()
    catalog = client.get("/api/v1/games/")
    assert catalog.status_code == 200
    assert catalog.data == {
        "schemaVersion": 1, "totalItems": 1,
        "items": [{
            "gameId": "tekken8", "slug": "tekken-8",
            "publicationState": "published", "name": "Tekken 8",
            "shortName": "Tekken",
            "description": game.description,
            "platforms": ["PS5", "PC"], "coverImage": None, "tournamentCount": None,
        }],
    }
    detail = client.get("/api/v1/games/tekken-8/")
    assert detail.status_code == 200
    assert detail.data["id"] == "tekken8"
    assert detail.data["competitiveFormats"][0]["id"] == "one-on-one"
    assert detail.data["stats"]["rankedPlayerCount"] == 0
    assert detail.data["tournaments"] == []
    assert client.get("/api/v1/games/tekken-8/").data == detail.data
    for sensitive in ["phone", "email", "user", "permissions", "wallet", "paymentUrl"]:
        assert sensitive not in str(detail.data)


@pytest.mark.django_db
def test_publication_visibility_and_game_slug_not_exposed():
    make_game(state="draft")
    make_game(slug="mortal-kombat", state="archived", game_id="mk")
    client = APIClient()
    assert client.get("/api/v1/games/").data["items"] == []
    for slug in ["tekken-8", "mortal-kombat", "unknown"]:
        assert client.get(f"/api/v1/games/{slug}/").status_code == 404
    assert client.post("/api/v1/games/", {}, format="json").status_code == 405


@pytest.mark.django_db
def test_validated_filters_and_indexed_search():
    make_game()
    make_game(slug="counter-strike-2", game_id="cs2", sort_order=3)
    client = APIClient()
    cases = [
        ("q=Tekken", ["tekken8", "cs2"]),
        ("platform=PS5", ["tekken8", "cs2"]),
        ("platform=Xbox", []),
        ("gameId=cs2", ["cs2"]),
        ("slug=tekken-8", ["tekken8"]),
    ]
    for query, expected in cases:
        response = client.get(f"/api/v1/games/?{query}")
        assert response.status_code == 200
        assert [item["gameId"] for item in response.data["items"]] == expected

    for query in ["q=", "q=%00", "gameId=bad$id", "slug=BadSlug", "unused=1",
                  "q=hi&q=there", "platform=%0A", "slug=tekken-8&slug=tekken-8"]:
        response = client.get(f"/api/v1/games/?{query}")
        if query == "q=":
            assert response.status_code == 200
        else:
            assert response.status_code == 400


@pytest.mark.django_db
def test_model_validation_and_slug_immutability():
    game = make_game()
    game.slug = "new-slug"
    with pytest.raises(ValidationError):
        game.save()
    game.refresh_from_db()
    game.platforms = ["PS5", "PS5"]
    with pytest.raises(ValidationError):
        game.save()
    game.platforms = []
    with pytest.raises(ValidationError):
        game.save()
    game.platforms = ["PS5"]
    game.description = "tiny"
    with pytest.raises(ValidationError):
        game.save()
    assert Game.objects.count() == 1


@pytest.mark.django_db
def test_home_projection_never_claims_cross_domain_counts():
    make_game()
    response = APIClient().get("/api/v1/discovery/home/")
    assert response.status_code == 200
    data = response.data
    assert data["schemaVersion"] == 1
    assert data["finder"]["games"] == [
        {"gameId": "tekken8", "slug": "tekken-8", "name": "Tekken 8"}
    ]
    assert data["popularGames"] == []
    assert data["featuredTournaments"] == []
    assert data["featuredGamingCenters"] == []
    assert "stats" not in data
    assert "rankingPreview" not in data
    assert APIClient().get("/api/v1/discovery/home/?foo=1").status_code == 400


@pytest.mark.django_db(transaction=True)
def test_racing_duplicate_slug_is_rejected_at_database_boundary():
    barrier = Barrier(2)

    def create(i):
        close_old_connections()
        barrier.wait(timeout=15)
        try:
            make_game(game_id=f"player{i}")
            return "ok"
        except (IntegrityError, ValidationError):
            return "rejected"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(create, [1, 2]))
    assert sorted(outcomes) == ["ok", "rejected"]
    assert Game.objects.filter(slug="tekken-8").count() == 1


@pytest.mark.django_db
def test_b03_schema_migrations_and_postgres_search_index_were_applied():
    """Prove test DB migrated both owned apps and installed the real PostgreSQL GIN index."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT app FROM django_migrations
            WHERE name = '0001_initial' AND app IN ('games', 'rulesets')
            ORDER BY app
            """
        )
        assert [row[0] for row in cursor.fetchall()] == ["games", "rulesets"]
        cursor.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'games_game' AND indexname = 'games_public_search_idx'
            """
        )
        assert cursor.fetchone() == ("games_public_search_idx",)
