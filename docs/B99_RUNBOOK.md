# B99 — Operational integration acceptance runbook

Status: **IN PROGRESS; NOT BACKEND FINAL/FROZEN**. Issue [#77](https://github.com/sajadkhavas/turnoment-backend/issues/77).

## Frozen inputs and known evidence
- Backend START/main: `436cc7281fc7c4a64c14cca604f06c94327a0600`.
- Frontend accepted snapshot: `1668109bae5ec7abb5e022e5857ffa65cc131501`, with explicit nullable/unranked compatibility correction in frontend PR #122.
- B01 freezes the active frontend contract in `apps.core.frontend.FROZEN_FRONTEND_CONTRACT_SHA`. The legacy P00 `/api/v1/system/meta/` SHA (`8d5736d788235e3e99765a5332f79f0cba861482`) is intentionally preserved; changing it would violate P00 compatibility.
- Last pre-B99 main quality: GitHub Actions [38226631690](https://github.com/sajadkhavas/turnoment-backend/actions/runs/38226631690), Python 3.12/3.14 PASS.
- Financial execution remains disabled: no payments, wallet, settlement, payouts, prizes or wagering.

## Applied B08 → B09 ranking truth
1. Provision exactly **one** unambiguous `Season` for each finalization timestamp, with non-overlapping historical windows. `is_published` controls public visibility; it must not substitute for an actual season policy.
2. Run `python manage.py drain_b08_events --limit 100` **after** `migrate`, regularly under an operational scheduler until the output is `Applied 0 B08 events.`. Use the matching production settings/environment.
3. The service iterates `FinalizedResultEvent` sorted by `finalized_at, id`; `AppliedMatchEvent` uniquely receipts event and match identities. Repeated invocation is safe. Do not replay events out of order or backdate old events after newer events are already applied.
4. A missing/ambiguous season, invalid result, or out-of-order event fails closed. **Do not** mark that event as consumed or fabricate a rating. Repair the exact domain records and retry; never delete receipts to erase history.
5. Production scheduler activation, lag metrics/alerts and chronological backfill policy require deployment-specific verification; this PR provides an explicit operator command, **not proof that a scheduler runs in production**.

## Repository gates
- Backend CI separately executes `manage.py migrate --noinput` against empty PostgreSQL 17 and then full `pytest`, lint, compile, Django, migration drift and production checks on Python 3.12 and 3.14.
- `apps/rankings/tests/test_b99_integration.py` establishes two separate session cookies and CSRF protections; uses 30 genuine B08 finalizations to unlock B07; performs real opponent discovery, invitation, unique match, score submission, counterparty confirmation, durable B09 drain and replay, public leaderboard, private B02 dashboard, and outsider denial.
- B04 center-object permissions, B10 operator-only moderation and negative dispute paths have domain tests. A single full cross-domain smoke test and browser test remain separate gates.

## Outstanding before closing #77
- Browser Playwright in API adapter mode with two genuinely independent front-end sessions, not only DRF test clients.
- Production scheduler/backfill operator setup, season overlap prevention/migration policy and monitoring.
- End-to-end B04/B05/B06/B08/B10 domain bridge verification and rejection cases against real APIs.
- Frontend ↔ backend runtime contract audit, exact final CI and merged SHA, full issue/registry closeout.
- Final user-assisted VS Code smoke acceptance.

References: [Django management commands](https://docs.djangoproject.com/en/6.1/howto/custom-management-commands/), [Django migrations](https://docs.djangoproject.com/en/6.1/topics/migrations/), [Celery periodic tasks](https://docs.celeryq.dev/en/main/userguide/periodic-tasks.html).
