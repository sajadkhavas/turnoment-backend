"""Disposable B99 operational Celery Beat -> Redis -> worker -> PostgreSQL acceptance.

Executed only with the explicit local E2E database safety contract.
Never invoke against production, staging, or user data.
"""

import os
import time

from django.conf import settings
from django.db import connection

from apps.rankings.models import AppliedMatchEvent, PlayerRating
from apps.rankings.tasks import drain_verified_b08
from apps.results.models import FinalizedResultEvent

database = connection.settings_dict
assert (
    os.getenv("B99_BROWSER_ONLY") == "1"
    and os.getenv("B99_ENABLE_RANKING_DRAIN") == "1"
    and settings.DEBUG
    and str(database["NAME"]).endswith("_e2e")
    and database["HOST"] in ("127.0.0.1", "localhost")
), "B99 Celery operational acceptance requires disposable LOCAL E2E PostgreSQL"

schedule = settings.CELERY_BEAT_SCHEDULE["b99-drain-finalized-match-ratings"]
assert schedule["task"] == "apps.rankings.drain_verified_b08"
assert schedule["schedule"] == 60.0
assert schedule["kwargs"] == {"limit": 100}
assert FinalizedResultEvent.objects.count() == 30
assert AppliedMatchEvent.objects.count() == 0
assert not PlayerRating.objects.exists()

# No direct task call here: first application MUST arrive from the actual
# 60-second Beat schedule, via Redis broker and a separate Celery worker.
deadline = time.monotonic() + 145
while time.monotonic() < deadline:
    applied = AppliedMatchEvent.objects.count()
    if applied == 30:
        break
    assert applied == 0, f"Partial ranking batch observed: {applied}"
    time.sleep(2)
else:
    raise AssertionError("Timed out waiting for real Celery Beat/worker to drain 30 B08 events")

ratings = list(
    PlayerRating.objects.filter(kind="tournament").order_by("user_id")
    .values_list("user_id", "rating", "played", "wins", "losses", "draws")
)
assert len(ratings) == 2, ratings
assert all(row[2] == 30 and row[5] == 0 for row in ratings), ratings
assert sorted((row[3], row[4]) for row in ratings) == [(0, 30), (30, 0)]
assert sum(row[1] for row in ratings) == 2000

snapshot = ratings
for attempt in range(2):
    result = drain_verified_b08.apply_async(kwargs={"limit": 100}).get(timeout=35)
    assert result == {"applied": 0, "skipped": None}, (attempt, result)
    assert AppliedMatchEvent.objects.count() == 30
    assert list(
        PlayerRating.objects.filter(kind="tournament").order_by("user_id")
        .values_list("user_id", "rating", "played", "wins", "losses", "draws")
    ) == snapshot, "Replay changed materialized ranking state"

assert AppliedMatchEvent.objects.count() == FinalizedResultEvent.objects.count() == 30
print("B99 CELERY BEAT WORKER PASS: scheduled 30 chronological B08 events, replay 0, ratings unchanged", flush=True)
