import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.games.models import Game
from apps.rulesets.models import Ruleset

SECTIONS = [{
    "id": "fair-play",
    "title": "Fair play",
    "description": "Respect competitors and referees.",
    "rules": [{"id": "no-cheating", "title": "No cheating", "body": "Play fairly."}],
}]


def make_policy(**overrides):
    params = {
        "key": "general-rules", "revision": "2026-10", "publication_state": "published",
        "title": "General tournament rules", "summary": "Public participation rules.",
        "sections": SECTIONS,
    }
    params.update(overrides)
    return Ruleset.objects.create(**params)


@pytest.mark.django_db
def test_public_ruleset_list_detail_and_private_exclusion():
    policy = make_policy()
    make_policy(key="staff-policy", revision="v1", publication_state="draft")
    client = APIClient()
    result = client.get("/api/v1/rulesets/")
    assert result.status_code == 200
    assert result.data["totalItems"] == 1
    assert result.data["items"][0]["policyId"] == str(policy.id)
    assert result.data["items"][0]["gameId"] is None
    assert client.get("/api/v1/rulesets/general-rules/").data["sections"] == SECTIONS
    assert client.get("/api/v1/rulesets/staff-policy/").status_code == 404
    assert client.post("/api/v1/rulesets/", {}).status_code == 405
    assert client.get("/api/v1/rulesets/?foo=1").status_code == 400
    assert client.get("/api/v1/rulesets/").data == result.data


@pytest.mark.django_db
def test_policy_published_key_is_exclusive_and_revision_distinct():
    make_policy()
    with pytest.raises(ValidationError):
        make_policy(revision="v2")
    with pytest.raises(ValidationError):
        make_policy()
    assert Ruleset.objects.count() == 1


@pytest.mark.django_db
def test_section_key_validation_and_non_published_game_rules_hidden():
    game = Game.objects.create(
        id="not-public", slug="unpublished-game", name="Hidden", short_name="Hidden",
        description="A private game not yet available.", platforms=["PC"],
    )
    policy = make_policy(game=game)
    result = APIClient().get("/api/v1/rulesets/")
    assert result.status_code == 200
    assert result.data["items"] == []
    assert APIClient().get(f"/api/v1/rulesets/{policy.key}/").status_code == 404
    broken = [dict(SECTIONS[0], rules=[SECTIONS[0]["rules"][0]] * 2)]
    policy.sections = broken
    with pytest.raises(ValidationError):
        policy.save()
