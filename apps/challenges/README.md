# B07 — Free in-person Challenge (Issue #53)

Branch: `phase/b07-challenges-opponent-search`
Source of frontend shape: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`
and `src/lib/challenge-hub-contract.ts`, `src/lib/challenge-hub-http-repository.ts`.
Baseline backend: `0f5d44646b608106ad20db97ec8c559fa084e6ce`.

## Endpoints (all private P01 SessionAuthentication + CSRF for writes)

- GET/POST `/api/v1/me/challenges/`
- GET `/api/v1/me/challenges/opponents/?q=&game=`
- POST `/api/v1/me/challenges/<uuid>/response/`
- POST `/api/v1/me/challenges/<uuid>/cancel/`

No public endpoint; list is actor-scoped and opponent search shows gamer tag only.
The challenge is free, face-to-face and non-financial. Extra request fields are rejected.

## B07 authoritative lifecycle

pending -> accepted (and exactly one B08 Match) | declined | cancelled | expired
accepted -> completed (only upon B08 authoritative finalized-Match callback).
Completed is immutable; terminal invitations cannot be reopened. Acceptance failure
or B08 outage must roll back completely and leave invitation pending.

Revision changes on every transition. The pending response/cancel mutation requires
the current revision and an actor-authorized command. All mutation attempts use
an `Idempotency-Key`; unique (actor,key) persistence stores a fingerprint and
the successful typed receipt. Identical retries replay; key/payload conflicts
are rejected. For symmetric duplicate invitations we lock both account rows
in deterministic PK order, then enforce the DB partial unique index on
canonical (low_player_uuid, high_player_uuid, game_id) for pending/accepted.
Expired invites are only physically expired inside writes; GET never mutates.

## Explicit B99 seams, NOT implemented fake providers

`apps/challenges/integrations.py` defines and currently fails closed for:
- `player_challenge_stats(user) -> PlayerChallengeStats`: B08 finalized *valid*
  match count and B09 separate Challenge Rating. Hard unlock threshold 30.
- `creation_games(user) -> tuple[GameChoice,...]`: reads actual published B03 games and solo-compatible formats.
- `opponent_eligible(challenger,opponent,game_id)->bool`: B02/B03/B08 server policy.
- `create_match_for_challenge(challenge)->matchId`: B08 must provide a
  **synchronous**, transactional, exactly-one match keyed by Challenge.id.
  It is invoked under B07 row lock in `transaction.atomic()`. B08 owns
  its table and a unique constraint on challenge origin. No fake match ID.
  No asynchronous transaction-critical creation.
- `services.record_finalized_match(challenge_id,match_id,...)`: B08 callback,
  only for finalized match in its transaction; stable replay, conflict failure.
  B08 must supply real outcome, score and (optional) rating deltas.

Even though B08 finalized-match counts and B09 scoped ratings are now real, creation remains locked until B99 approves a truthful schedule and B08 synchronous adapter,
and any already-stored pending invite cannot be accepted without B08.
B99 must wire the real providers and complete full-stack smoke tests.

## Tests / security gates

The pytest suite supplies isolated test providers through monkeypatch. It tests
the locked and no-B08 fail-closed production baseline as well as authorization,
privacy, exact response schemas, CSRF, invalid financial fields, replay/key
reuse, self-challenge, canonical duplicate prevention, expiry, status/revision,
finalization callback and PostgreSQL threaded create/accept races.

Expected CI: `ruff check .`, `python -m compileall -q apps config manage.py`,
`python manage.py check`, `python manage.py makemigrations --check --dry-run`,
`pytest -q`, and production `check --deploy --fail-level WARNING`.
Requires PostgreSQL for row-lock and partial-unique-index behavior.

## Official sources consulted

- Django transactions: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django QuerySet select_for_update: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#select-for-update
- Django constraints: https://docs.djangoproject.com/en/6.1/ref/models/constraints/
- DRF permissions: https://www.django-rest-framework.org/api-guide/permissions/
- DRF SessionAuthentication + CSRF: https://www.django-rest-framework.org/api-guide/authentication/
- DRF serializer validation: https://www.django-rest-framework.org/api-guide/serializers/
- PostgreSQL partial unique indexes: https://www.postgresql.org/docs/current/indexes-partial.html

B07's official-source decisions are now reconciled into `docs/OFFICIAL_SOURCES.md` in the mother-review branch.

FINANCIAL EXECUTION ADDED: NO
