# B00 — Final Backend Execution Lock

Status: `READY FOR REVIEW — EXECUTION PLAN LOCKED`

Tracking Issue: `#45`

Backend repository: `sajadkhavas/turnoment-backend`

B00 START_SHA: `46b3f47b38068675ed8a0941a871438e51abd6a2`

B00 branch: `phase/b00-final-backend-execution-lock-20261010`

Frozen frontend repository: `sajadkhavas/turnoment`

Frozen frontend contract SHA: `1668109bae5ec7abb5e022e5857ffa65cc131501`

## 1. Purpose

B00 replaces the old sequential “next phase only” execution assumption with a controlled ten-workstream backend build while preserving the accepted P00/P01 foundation and the final frozen frontend contract.

The backend remains a Django/DRF modular monolith backed by PostgreSQL, Redis and Celery. The final frontend contract is immutable for this execution wave: backend implementation adapts to it unless a demonstrable contract bug is found and explicitly approved by the integration owner.

## 2. Non-negotiable financial exclusion

Financial execution is intentionally deferred. No B00 workstream may implement, activate, simulate as successful, or silently stub a real-money flow.

Forbidden in this execution wave:

- payment gateway/provider integration;
- payment intents/orders/callback verification;
- wallet, user balance or user-to-user transfer;
- ledger-based money movement;
- refund execution;
- participant-funded prize pools;
- prize payout/disbursement;
- gaming-center settlement/payout;
- commission settlement;
- real payment links or `paymentUrl` generation;
- betting, wagering, odds, stake or challenge-for-money behavior.

Existing frontend fields such as `entryFee`, `fixedPrize` and the reserved `payment_required` result remain compatibility metadata only. Backend models may preserve non-floating integer money fields where required by the immutable read contract, but MUST NOT create a financial state machine.

Paid tournament registration remains `BACKEND_PENDING_FINANCE`. Workstreams must not falsely confirm a paid registration. Local end-to-end acceptance uses free tournaments.

Challenge is always non-monetary.

## 3. Global engineering law

All workstreams:

1. start from the exact B00 frozen head after B00 is merged;
2. use a dedicated branch and GitHub Issue/PR;
3. preserve `/api/v1/`;
4. preserve P01 SessionAuthentication + CSRF behavior;
5. enforce server-side authorization and object/center scope;
6. use PostgreSQL as durable business truth;
7. enforce database-suitable invariants with constraints/indexes;
8. wrap race-prone state transitions in `transaction.atomic()` and evaluate `select_for_update()`;
9. make retryable mutation commands idempotent where duplicate delivery is possible;
10. keep Celery for asynchronous side effects only, never critical committed truth;
11. add positive, negative, permission, state-transition and failure-path tests;
12. never expose private identity fields through public projections;
13. never infer frontend-visible business truth in the client;
14. do not modify another workstream's domain files except through an explicit integration handoff.

Official implementation references include Django 6.1 transaction/database guidance, Django REST Framework authentication/permissions/serializers/throttling guidance, PostgreSQL constraints/locking guidance and Celery task guidance.

## 4. Shared-file collision rule

The ten domain chats may develop in parallel. Their primary ownership is under `apps/<owned-domain>/` plus domain-specific docs/tests.

Shared files are integration-owned:

- `config/settings/*`
- `config/urls.py`
- root dependency files
- shared CI/workflow definitions
- `PROJECT_CONTINUITY.md`
- `docs/PHASE_REGISTRY.md`
- global contract/architecture docs

A domain branch may include the minimum shared wiring required to execute its branch tests, but its final handoff MUST list every shared-file change. The mother/integration agent resolves and normalizes shared wiring during merge; domain agents must not refactor unrelated shared code.

## 5. Ten workstreams

### B01 — Core Contract & Integration Foundation
Owns shared API conventions, common pagination/error helpers, cross-domain identifiers, audit primitives, test helpers, integration wiring conventions and final frontend-baseline alignment. No business-domain replacement of P01.

Primary ownership: `apps/core/`, `apps/audit/`, shared integration helpers. Shared config changes are permitted only for core plumbing.

### B02 — Accounts / Player / Settings
Extends frozen P01 without replacing it. Owns current-player dashboard identity projections, profile compatibility, notification preferences, public-player projection compatibility and role primitives required by player vs center staff.

Primary ownership: `apps/accounts/` extensions and `apps/players/`.

### B03 — Games / Rules / Public Discovery
Owns games catalog/detail, game policies/rulesets and backend projections required by public home discovery.

Primary ownership: `apps/games/`, `apps/rulesets/`, discovery projections directly dependent on them.

### B04 — Gaming Centers / Host / Resources
Owns public center discovery/detail, host application persistence, center profile/resources/stations/hours, center staff memberships and center-scoped permissions.

Primary ownership: `apps/gaming_centers/`, `apps/gaming_resources/`.

Central Django/platform admin remains separate from center staff permissions.

### B05 — Tournaments / Registration / Check-in / Brackets
Owns tournament discovery/detail, free registration, capacity reservation, current-player tournament list, check-in and bracket/round structure.

Primary ownership: `apps/tournaments/`, `apps/registrations/`, `apps/checkins/`, `apps/brackets/`.

Financial execution is forbidden. Paid registration stays pending; no payment URL.

### B06 — Teams / Membership / Achievements
Owns player teams, team membership/roles/invites where required by frozen contracts, and non-financial achievement definitions/progress.

Primary ownership: `apps/teams/`, `apps/achievements/`.

### B07 — Challenges / Opponent Search
Owns challenge list/search/create/respond/cancel and challenge lifecycle. Accepted challenges create exactly one match through an explicit service boundary supplied by the matches domain/integration layer.

Primary ownership: `apps/challenges/`.

No challenge money, stake, bet or prize behavior.

### B08 — Matches / Results / Disputes
Owns player match list, match lifecycle, result read/submission/confirmation/finalization, dispute creation/read/evidence and transition safety.

Primary ownership: `apps/matches/`, `apps/results/`, `apps/disputes/`.

Finalization is atomic and emits a stable domain event/record for rankings. Duplicate submissions/finalizations must not create duplicate effects.

### B09 — Rankings / Stats / Rivalries
Owns rating/ranking events, public ranking, player competitive stats and rivalry projections derived from finalized match truth.

Primary ownership: `apps/rankings/`, `apps/rivalries/`.

A finalized match affects ranking exactly once.

### B10 — Notifications / Moderation / Admin Operations
Owns notification persistence/read/read-all, moderation/audit-facing operational models, Django admin registrations and operator APIs needed to review host applications, disputes and platform content without granting center staff central-admin authority.

Primary ownership: `apps/notifications/`, `apps/moderation/`, admin registrations and operational projections.

## 6. Dependency graph

- B01 is the common convention provider.
- B02 and B03 can proceed immediately.
- B04 depends only on B01/B02 role primitives.
- B06 depends on B02 and B03.
- B05 depends on B02/B03/B04 and optionally B06 for team registration.
- B08 depends on B02/B03/B04 and match identities created by B05/B07.
- B07 depends on B02/B03 and the B08 match-creation service contract.
- B09 depends on B08 finalized-result truth.
- B10 consumes events/objects from all domains but must not own their business transitions.

Parallel implementation is allowed; dependency interfaces must be documented and integration-owned rather than solved by cross-editing another domain.

## 7. Frozen frontend endpoint map

The frozen frontend expects, among others:

- auth/session/CSRF under `/api/v1/auth/*`;
- `GET /api/v1/me/dashboard/`;
- `GET /api/v1/games/` and game detail;
- `GET /api/v1/centers/` and center detail;
- `POST /api/v1/host-applications/`;
- `GET /api/v1/tournaments/`;
- tournament detail, registration context and registration command;
- `GET /api/v1/me/tournaments/`;
- `GET /api/v1/me/matches/`;
- result GET/POST;
- dispute GET/POST/evidence;
- challenge list/opponent search/create/respond/cancel;
- `GET /api/v1/rankings/`;
- public player profile;
- player teams/achievements/rivalries;
- notifications list/read/read-all;
- notification preferences GET/PATCH;
- `GET /api/v1/discovery/home/`.

Exact request/response shapes are sourced from frontend SHA `1668109bae5ec7abb5e022e5857ffa65cc131501`, not from stale backend prose.

## 8. Per-workstream acceptance

Every chat must return:

- branch name and exact START_SHA/END_SHA;
- owned files changed;
- migrations created;
- endpoints implemented;
- permission matrix tested;
- state transitions/invariants tested;
- concurrency/idempotency tests where applicable;
- commands run and exact pass/fail results;
- unresolved blockers/dependencies;
- shared-file changes requiring integration attention;
- confirmation that financial execution was not added.

No chat may claim global backend completion.

## 9. Mother/integration acceptance (B99)

After ten workstreams are reviewed and merged into the integration branch:

1. migrations apply from empty PostgreSQL;
2. Django checks + migration drift + full tests pass;
3. final frontend runs in API adapter mode against local backend;
4. two independent browser sessions register/login as different players;
5. Player A finds Player B and sends a challenge;
6. Player B sees it in their own session and accepts/declines;
7. accepting creates exactly one match visible to both;
8. result workflow reaches authoritative finalization without duplicate effects;
9. ranking/stat projection updates exactly once;
10. dispute negative/permission paths pass;
11. a center/operator account can access only its center-scoped resources/operations;
12. center staff cannot access platform-admin authority;
13. public endpoints expose no private PII;
14. no payment/wallet/settlement/prize-payout execution exists;
15. paid-registration path remains explicitly disabled/pending;
16. final frontend contract tests remain compatible.

Only the mother/integration agent can declare `BACKEND FINAL / FROZEN`.
