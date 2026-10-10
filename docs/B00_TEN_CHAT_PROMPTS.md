# B00 — Copy-Ready Prompts for 10 Parallel Backend Chats

All ten chats use the same immutable baselines:

- Backend repository: `sajadkhavas/turnoment-backend`
- B00 tracking Issue: `#45`
- Backend baseline before B00: `46b3f47b38068675ed8a0941a871438e51abd6a2`
- Final frontend contract: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`
- Stack: Django + DRF + PostgreSQL + Redis + Celery
- Read first: `PROJECT_CONTINUITY.md`, `PHASE_COMPLETION_PROTOCOL.md`, `docs/B00_FINAL_BACKEND_EXECUTION_LOCK.md`, `docs/ENGINEERING_RULES.md`
- Absolute financial rule: DO NOT implement payment gateway, payment intent, wallet, ledger money movement, refund execution, prize payout, center settlement, betting/wagering, or real payment URLs. Paid registration remains pending. Challenge is always free/non-monetary.

Each chat must work on its own branch, tests and handoff. Never claim the entire backend is finished.

---

## Chat 01 — B01 Core Contract & Integration Foundation

You own B01 only. Create a dedicated branch from the exact merged B00 head. Reconcile the backend runtime baseline with the frozen frontend SHA `1668109bae5ec7abb5e022e5857ffa65cc131501`. Implement only reusable backend integration primitives that other domains can consume: consistent API error shape, pagination helpers if needed, stable identifier conventions, audit/event primitives, shared test utilities and minimal shared routing/settings conventions. Preserve P01 authentication behavior. Do not implement another domain's models. Do not implement finance.

Review current official Django/DRF/PostgreSQL guidance before coding. Prefer DB constraints for invariants, atomic service-layer transitions and explicit permissions. Add tests for the core helpers you create. Report exact START/END SHA, changed files, test commands, CI state and a concise integration contract for the other nine chats.

---

## Chat 02 — B02 Accounts / Player / Settings

You own B02. Build on P01; do not rewrite OTP/session authentication. Implement the frozen frontend contracts for current-player identity/dashboard needs, player profile compatibility, public-player privacy projection, notification preferences, and role primitives needed to distinguish player, center staff/manager and platform operator. Use SessionAuthentication/CSRF and server-side permissions. Keep public PII sealed.

Primary files belong in `apps/accounts/` and `apps/players/`. Avoid unrelated shared refactors. Add positive/negative/privacy/permission tests and any migrations. No finance. Handoff exact endpoint matrix and role/permission matrix.

---

## Chat 03 — B03 Games / Rules / Public Discovery

You own B03. Implement authoritative game catalog/detail and ruleset/game-policy models/projections matching the frozen frontend contracts. Implement the game-owned portion of public discovery/home data without inventing mutable frontend truth. Public endpoints must explicitly declare correct public permissions under the authenticated global default.

Primary ownership: `apps/games/`, `apps/rulesets/`. Add filtering/search/indexes required by contract and tests for public access, validation and stable IDs/slugs. Do not implement tournaments, centers or finance; expose clean service/query interfaces for them.

---

## Chat 04 — B04 Gaming Centers / Host / Resources

You own B04. Implement public gaming-center discovery/detail, host application persistence, gaming-center profile, systems/stations/resources/hours and center staff membership/scope. Implement the frozen `POST /api/v1/host-applications/` contract with server-side validation, abuse controls and privacy. Center manager/staff permissions must be object-scoped; they are never central platform admins.

Primary ownership: `apps/gaming_centers/`, `apps/gaming_resources/`. Add DB constraints, uniqueness, permission tests and public/private projection tests. Do not implement payments or settlements.

---

## Chat 05 — B05 Tournaments / Registration / Check-in / Brackets

You own B05. Implement tournament discovery/detail, capacity/lifecycle, free registration, current-player tournament projection, check-in, bracket/round structures and team-registration hooks needed by the frozen frontend.

Use transaction boundaries and row locks for capacity/race-prone registration. Preserve `entryFee`/`fixedPrize` read fields only if required by the frozen contract, using integer accounting units. Do NOT implement payment or generate `paymentUrl`. Any tournament requiring payment must remain explicitly non-confirmable/pending finance. Build local acceptance around free tournaments.

Primary ownership: `apps/tournaments/`, `apps/registrations/`, `apps/checkins/`, `apps/brackets/`. Add concurrency, capacity, duplicate-registration, permission and lifecycle tests.

---

## Chat 06 — B06 Teams / Membership / Achievements

You own B06. Implement the frozen player-team projection and required team membership/role/invite domain needed for team tournaments, plus non-financial achievement definitions/progress required by the frontend. Enforce membership permissions and stable team IDs.

Primary ownership: `apps/teams/`, `apps/achievements/`. Do not implement challenge, match, ranking or finance logic. Expose narrow interfaces other domains can consume. Add permission, duplicate membership/invite and privacy tests.

---

## Chat 07 — B07 Challenges / Opponent Search

You own B07. Implement challenge list/filter, opponent search, create, respond and cancel exactly as the frozen challenge-hub contract requires. Challenge is an invitation/coordination object for an in-person game: absolutely no stake, fee, bet, odds, prize or money field.

Design a strict challenge state machine and enforce object authorization. Acceptance must be idempotent and create exactly one match through a documented service boundary; if B08 is not yet available, provide the interface and integration test seam without implementing B08-owned match internals. Use atomic locking for accept/cancel races. Add concurrency, replay, self-challenge, duplicate-active-challenge and permission tests.

Primary ownership: `apps/challenges/`.

---

## Chat 08 — B08 Matches / Results / Disputes

You own B08. Implement current-player match projection, match lifecycle, result GET/POST contract, result confirmation/finalization states required by the frozen frontend architecture, and dispute read/create/evidence flows. Match truth is authoritative and must support both tournament-created and challenge-created matches.

Use atomic transactions/row locks for state transitions; duplicate result submissions/finalization must not duplicate consequences. Emit a stable finalized-result event/record for B09 rather than directly owning ranking formulas. Evidence access must be permission-scoped and uploads treated as untrusted if implemented.

Primary ownership: `apps/matches/`, `apps/results/`, `apps/disputes/`. No finance.

---

## Chat 09 — B09 Rankings / Stats / Rivalries

You own B09. Implement rating/ranking event persistence, public ranking projection, public/player competitive stats required by frozen contracts and rivalry projections derived from authoritative finalized matches. Consume B08 finalized-result truth through a stable idempotent interface.

A finalized match may affect ranking exactly once. Protect against duplicate delivery/replay with a DB constraint/idempotency key and transactional update. Add deterministic rating tests, duplicate-event tests, permission/privacy tests and leaderboard ordering/index tests.

Primary ownership: `apps/rankings/`, `apps/rivalries/`. No financial rewards.

---

## Chat 10 — B10 Notifications / Moderation / Admin Operations

You own B10. Implement notification persistence and frozen list/read/read-all behavior, plus operational moderation/audit/admin surfaces needed by platform operators to review host applications, disputes and managed content. Register appropriate models in Django admin. Center staff must never gain central platform-admin access.

Notifications are side effects/projections; Celery may deliver asynchronous notifications, but business-state commits remain synchronous in owning domains. Make notification generation idempotent where events can be retried. Add permission, unread-count/read-all, moderation-scope and admin-access tests.

Primary ownership: `apps/notifications/`, `apps/moderation/` and domain admin registrations. No finance.

---

## Mandatory handoff template for every chat

Return exactly these facts at completion:

1. Workstream and branch.
2. START_SHA and END_SHA.
3. Files changed, grouped by owned vs shared.
4. Migrations.
5. Endpoints and methods.
6. DB invariants/constraints.
7. Transaction/idempotency decisions.
8. Authentication/permission matrix.
9. Tests added and exact command results.
10. CI/PR/Issue status.
11. Dependencies still waiting on another workstream.
12. Any shared-file conflict the mother agent must resolve.
13. Explicit statement: `FINANCIAL EXECUTION ADDED: NO`.
14. Do not claim global backend completion.
