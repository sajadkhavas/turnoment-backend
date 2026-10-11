# B09 — Rankings, competitive stats, rivalries (integration contract)

Source-of-truth frontend: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`.
Backend START_SHA: `ffe44e3d999479282115c4bebdb4f33b40f5a598`.
Owns apps/rankings and apps/rivalries only. Shared config/settings/base.py and config/urls.py are integration-owned and require B99 reconciliation.

## B08 consumption (not enabled until B08 is merged)

`apps.rankings.services.apply_b08_event(event_id)` fetches an actual persisted
`apps.results.models.FinalizedResultEvent`, verifies matching match participant
identity and completed lifecycle and converts it to the immutable B09
`FinalizedInput` DTO. The internal helper `apply_verified_finalization` is NOT
a public write interface and must only be called with verified B08 data; tests
construct explicit sample DTOs because B08 is not on current main.

`drain_b08_events(limit=100)` reads B08's outbox in finalized_at/id ordering.
B99 should invoke it from a trusted queue/scheduler, never an HTTP user command.
B09 must NOT modify B08 finalization or request a Celery task to commit B08 truth.
Out-of-order historical deliveries fail closed for a game/season/kind; B99 must
coordinate backfill ordering/rebuild policy before enabling production ingestion.
One `AppliedMatchEvent.source_event_id` and `source_match_id` each are globally
unique. The Season row lock serializes parallel consumers on PostgreSQL; a replay
reuses the persisted receipt after digest verification and never changes ratings.

Integer Elo v1: starting 1000, K=32, deterministic round-to-nearest of delta,
player B gets opposite delta; floor rating at zero. Tournament vs challenge have
fully independent scopes; finalized draw counts, cancelled/unfinalized/void do
not. Seasons must be configured as explicit non-overlapping windows; no synthetic
season is seeded. Rank movement is `flat/0` until a real prior rank snapshot
exists (not a fabricated change). Zero published games/seasons returns 503,
never fixtures.

## Public identity and privacy

A B09 `PublicRankingIdentity` is an explicit publication gate with immutable
public `username` and City relation; never interpret mutable P01 gamer_tag as
an immutable username. The public profile deliberately excludes private bio,
phone, email, avatar_key, permissions, OTP and unpublished opponent tags.
Coordinate with B02 before introducing overlapping public username APIs.
B09 publishes no identity by default. Published Games and Seasons are required.
B06 team-vs-team is deferred: currently only two distinct P01 accounts.

## Endpoints

GET /api/v1/rankings/ — anonymous, F21 typed ranking page; filters game/season/region/type/page.
GET /api/v1/me/rivalries/ — session only, F12 current-user rivalry aggregation.
GET /api/v1/players/{username}/public-profile/ — anonymous, F22 publication gate and snapshots.
No B09 public or private mutation endpoints.

Official references reviewed:
- https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- https://www.postgresql.org/docs/current/explicit-locking.html
- https://www.django-rest-framework.org/api-guide/permissions/
- https://www.django-rest-framework.org/api-guide/pagination/

No finance, wallet, payout, prize settlement, payment URL or betting behavior.
FINANCIAL EXECUTION ADDED: NO
