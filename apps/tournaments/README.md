# B05 — Tournaments, registrations, check-in and bracket integration

Frontend source of truth: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`.
Backend starting point: `0f5d44646b608106ad20db97ec8c559fa084e6ce`.
Issue: https://github.com/sajadkhavas/turnoment-backend/issues/51

## Ownership and contracts

- `GET /api/v1/tournaments/`: public discovery with normalized query, pagination, metadata and capacity.
- `GET /api/v1/tournaments/{slug-or-uuid}/`: public detail including rules, participants' public gamer tags, bracket preview, and read-only IRR amounts.
- `GET /api/v1/tournaments/{slug-or-uuid}/registration/`: session-authenticated context and teams eligible through B06 adapter.
- `POST /api/v1/tournaments/{slug-or-uuid}/registrations/`: authenticated + CSRF, free-only, retry-safe.
- `GET /api/v1/me/tournaments/`: session-authenticated own registrations and next actions.
- `GET|POST /api/v1/tournaments/{slug-or-uuid}/check-in/`: own-confirmed-registration only.

`Tournament.game_key` and `Tournament.center_key` are non-FK integration seams for B03/B04 until their models and stable public IDs land. Snapshot columns must be populated by integration-owner seeding from authoritative B03/B04 data. No edits to those domains and no guessing model interfaces.

B06 team hook is configured with `TOURNAMENT_TEAM_ELIGIBILITY_HOOK`, a dotted path to a callable `(user, tournament) -> iterable[dict]`. Required dict members: `id`, `name`, `memberCount`, `role`. Only a captain can register. Default without B06 is deny-by-default empty teams. B08 consumes `apps.brackets.services.publish_round` for seeding and owns match outcomes.

## Invariants

- PostgreSQL lock on tournament row before checking duplicate/capacity. A unique `(tournament, user)` registration exists even if cancelled; a cancelled row may be reactivated under the same lock.
- `0 <= registered_count <= capacity` enforced in DB, `capacity > 0`, unique bracket round number, unique match position, and unique check-in per registration.
- Lifecycle transition service is atomic, explicitly enumerated, and replay-safe. Neither frontend nor unauthenticated public clients can change lifecycle or bracket outcomes.
- Players may check in only for their own confirmed registration during the opening window; retry returns the initial checked-in timestamp.
- `entryFee` and `fixedPrize` are IRR integer read metadata only. Any `entryFee > 0` stays `BACKEND_PENDING_FINANCE`, returns unavailable, and never creates confirmed registration, paymentUrl, payout or financial record.
- No user phone or email in public tournament projections. Public participant aliases are gamer tags or anonymized stable fallbacks.

## Known integration boundaries

The frozen frontend has no standard self-service check-in HTTP adapter, but B05 exposes a secure, independently testable endpoint for later wiring. Frontend frozen union includes a legacy `payment_required` success variant with `paymentUrl`; B05 **never** emits it and returns `unavailable` with pending-finance metadata instead. This is a deliberate financial exclusion, not permission to implement payment.

CI must run `ruff check .`, Django `check`, `makemigrations --check --dry-run`, `pytest -q`, and production checks under PostgreSQL 17 / Python 3.12 and 3.14. Tests under `apps/registrations/tests/test_concurrency.py` require a real PostgreSQL database for row-lock semantics.
