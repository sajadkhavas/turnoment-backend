"""Explicitly opt-in, replay-safe B08 → B09 periodic projection consumer."""

import logging

from celery import shared_task
from django.db import connection, transaction

from apps.rankings.services import drain_b08_events

logger = logging.getLogger(__name__)
# Constant, application-specific advisory lock key; no cross-domain locks.
RANKING_DRAIN_LOCK = 909900001


@shared_task(name="apps.rankings.drain_verified_b08")
def drain_verified_b08(limit=100):
    """One chronological batch, serialized even with multiple Celery workers.

    When another worker owns the lock, this invocation skips without marking
    any event consumed. Business truth stays inside B08's durable outbox.
    Exceptions remain visible to Celery instead of pretending success.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", [RANKING_DRAIN_LOCK])
            acquired = cursor.fetchone()[0]
        if not acquired:
            logger.info("B99 ranking drain skipped: another worker holds advisory lock")
            return {"applied": 0, "skipped": "locked"}
        applied = drain_b08_events(limit=limit)
        logger.info("B99 ranking drain applied %d verified B08 events", applied)
        return {"applied": applied, "skipped": None}
