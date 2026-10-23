"""Ephemeral B99 browser-test bootstrap. NEVER run on production data."""
import json
import os
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from apps.accounts.models import PlayerProfile, User
from apps.games.models import CompetitiveFormat, Game
from apps.gaming_centers.models import City
from apps.matches.services import advance_match, create_match_for_source
from apps.rankings.models import PublicRankingIdentity, Season
from apps.results.models import FinalizedResultEvent
from apps.results.services import confirm_score, submit_score

db = connection.settings_dict
if (
    os.getenv("B99_BROWSER_ONLY") != "1"
    or not settings.DEBUG
    or not str(db["NAME"]).endswith("_e2e")
    or db["HOST"] not in ("127.0.0.1", "localhost")
):
    raise RuntimeError("B99 browser seed blocked outside disposable LOCAL E2E database")

a = User.objects.create_user(phone="+989121010101")
b = User.objects.create_user(phone="+989121010102")
stranger = User.objects.create_user(phone="+989121010103")
for user, tag in ((a, "b99webalpha"), (b, "b99webbravo"), (stranger, "b99webthird")):
    PlayerProfile.objects.create(user=user, gamer_tag=tag)
game = Game.objects.create(
    slug="b99-browser-game", name="B99 Browser Game", short_name="Browser",
    description="Actual published game for real browser cross-domain acceptance.",
    platforms=["PC"], publication_state=Game.Publication.PUBLISHED,
)
CompetitiveFormat.objects.create(
    game=game, key="solo", label="Solo", description="Individual format",
    team_size=1,
)
Season.objects.create(
    slug="b99-browser-season", label="Real browser acceptance season",
    starts_at=timezone.now() - timedelta(days=1),
    ends_at=timezone.now() + timedelta(days=1),
    is_published=True,
)
city = City.objects.create(slug="b99-karaj", name="Karaj")
for user, username in ((a, "b99_web_alpha"), (b, "b99_web_bravo")):
    PublicRankingIdentity.objects.create(
        user=user, city=city, username=username, is_published=True,
        search_visibility="indexable",
    )

# Real B08 state transitions, not hand-written ranking/achievement data.
for number in range(30):
    match = create_match_for_source(
        source_kind="tournament", source_id=f"b99-browser-free-{number}",
        participant_a=a, participant_b=b, game_id=game.pk,
        game_name=game.name, competition_title="B99 free preparation games",
        starts_at=timezone.now() - timedelta(hours=1),
    )
    advance_match(match.pk, "ready")
    advance_match(match.pk, "awaiting-result")
    match.refresh_from_db()
    assert submit_score(
        match.pk, a, str(match.revision), 3, 1, f"b99-browser-seed-{number}",
    )["outcome"] == "accepted"
    match.refresh_from_db()
    assert confirm_score(
        match.pk, b, str(match.revision), 1, 3,
    )["outcome"] == "finalized"
assert FinalizedResultEvent.objects.count() == 30
data = {
    "phones": {
        "alpha": "+989121010101",
        "bravo": "+989121010102",
        "third": "+989121010103",
    },
    "gameId": game.pk,
    "gameSlug": game.slug,
    "season": "b99-browser-season",
    "tags": ["b99webalpha", "b99webbravo", "b99webthird"],
}
Path("/tmp/turnoment-b99-browser-seed.json").write_text(
    json.dumps(data), encoding="utf-8",
)
print("B99_BROWSER_SEED_CREATED 30 finalized B08 matches; no mock ratings")
