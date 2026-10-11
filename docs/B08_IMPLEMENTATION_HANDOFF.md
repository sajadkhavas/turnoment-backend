# B08 — Matches / Results / Disputes implementation handoff

Target frontend: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`.
Baseline backend: `0f5d44646b608106ad20db97ec8c559fa084e6ce`.
Ownership: `apps/matches/`, `apps/results/`, `apps/disputes/`.
Only shared runtime changes: register three app configs in `config/settings/base.py` and route five endpoints from `config/urls.py`. Other workstream domains untouched.

## Official references reviewed
- Django 6.1 transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django 6.1 select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- DRF parsers: https://www.django-rest-framework.org/api-guide/parsers/
- PostgreSQL row locks: https://www.postgresql.org/docs/current/explicit-locking.html

Decisions: wrap mutation services in `transaction.atomic`, lock the same match row before all changes, constrain match source identity and event uniqueness in PostgreSQL, require session/CSRF for authenticated writes, validate uploaded file signatures and restrict evidence to private quarantined DB blobs without public URLs. Binary evidence is unscanned/quarantined and MUST NOT be opened or served until approved malware scanning and private delivery are implemented in integration/operations.

## Integration seams
- B05/B07: call `apps.matches.services.create_match_for_source(...)` inside the source owner's atomic acceptance/bracket transaction. Source identity `(source_kind, source_id)` is unique. Supply `participant_a/b`, authoritative game/schedule/venue/competition snapshots. Call `advance_match(pk, target_state)` after authenticated source lifecycle verification; no public transition API. Match creation is NOT automatically inferred by F04 fixtures.
- B05 team matches: B06 team identity/membership integration is not yet available; present model supports 1v1 accounts only and team matchmaking must not be falsely reported as implemented.
- B09: read immutable `apps.results.models.FinalizedResultEvent` (unique `match_id`, `result_id`, score_a/b, player_a/b IDs, finalized_at). Derive ratings idempotently keyed by `event.id`; never recompute result truth or write finalization event from B09. Rating delta intentionally null until B09 projection.
- B10: `apps.disputes.services.start_review` and `resolve_dispute` require platform superuser; center staff never gain this authority. `adjusted` intentionally rejects without an explicit audited score-correction contract.
- No money, price, wallet, provider, payment URL or payout behavior.

## API mapping
- GET `/api/v1/me/matches/` query state/kind/game/page (self only).
- GET/POST `/api/v1/matches/<uuid>/result/` (participants only, header Idempotency-Key).
- POST `/api/v1/matches/<uuid>/result/confirm/` (counterparty only, score/revision validated; no F05 confirmation form yet).
- GET/POST `/api/v1/matches/<uuid>/dispute/` (participants only).
- POST `/api/v1/matches/<uuid>/dispute/<uuid>/evidence/` (participants only, multipart).
- All other participant access is 404; anonymous access denied; operator action only through service (B10 integration).

## Deferred / explicit blockers
- Backend B05/B07/B03/B04/B06 dependencies do not exist on frozen B00 main, so full source-connected tournament/challenge/team/venue acceptance is B99 integration pending.
- Reviewer evidence handling remains quarantined until scanning/private delivery is integrated; no public evidence download endpoint.
- Score adjustment moderator path deliberately fails closed until explicit B10-approved audit/reversion semantics.
- Full cross-app E2E acceptance belongs to B99; this branch is never the global backend freeze.

FINANCIAL EXECUTION ADDED: NO
