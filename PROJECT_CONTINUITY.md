# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-10`

## 1. Continuation law

Every backend chat/agent MUST:
1. read this file and `PHASE_COMPLETION_PROTOCOL.md`;
2. verify exact current `main` before mutation;
3. read `docs/PHASE_REGISTRY.md` before starting/reordering a backend phase;
4. use a dedicated branch/Issue/PR;
5. never claim DONE from chat memory;
6. keep cross-repo frontend contracts explicit without pretending planned APIs are live;
7. update continuity/evidence before ending;
8. preserve exact SHA/CI/PR/Issue evidence.

## 2. Repository truth

Backend repo: `sajadkhavas/turnoment-backend`

Current accepted backend main / F13 docs-alignment START_SHA:

`e81b13a0de6936ded0879d4310eab3883a7556a6`

That SHA contains P00/P01 plus completed F03/F04/F05/F06/F10/F11/F12 cross-repo contract documentation. It does **not** contain tournaments/matches/results/disputes/notifications/settings/rivalries/achievements runtime domain implementation.

F12 documentation alignment is terminally complete:
- Issue `#21` — CLOSED / COMPLETED;
- docs head `01ebe3832642799e5a040cf3420a47819d518078`;
- PR `#22` — MERGED;
- PR Quality Gate `34516235451` — PASS on Python 3.12 and 3.14;
- accepted backend main `e81b13a0de6936ded0879d4310eab3883a7556a6`;
- post-main Backend Quality Gate `34516995711` — PASS on Python 3.12 and 3.14;
- runtime remains `FRONTEND MOCK / BACKEND PENDING` for Rivalries.

Active backend workstream:
- `Cross-repo F13 — Player Achievements Hub contract alignment`;
- status: `IN PROGRESS — DOCUMENTATION ONLY`;
- START_SHA: `e81b13a0de6936ded0879d4310eab3883a7556a6`;
- branch: `docs/f13-player-achievements-contract`;
- Issue: `#23`;
- contract: `docs/F13_PLAYER_ACHIEVEMENTS_CONTRACT.md`;
- Python/models/migrations/serializers/views/URLs/dependencies/phase-registry mutation: `FORBIDDEN / NONE`.

Frontend F13:
- repo `sajadkhavas/turnoment`;
- route `/dashboard/achievements`;
- frontend START_SHA `a058de708c755d98e7180ffee616b50cbdd8598c` — F12 terminal frozen main;
- branch `phase/f13-player-achievements`;
- Issue `sajadkhavas/turnoment#68`;
- target `FINAL_PRIVATE`;
- runtime achievements endpoint remains `FRONTEND MOCK / BACKEND PENDING` until an owning backend phase implements it.

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`;
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`;
- Backend NEXT → `P02 — Games / Catalog Foundation`.

F03/F04/F05/F06/F10/F11/F12/F13 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as live runtime implementation.

## 4. Permanent product/auth law

Frontend architecture may finalize ahead of backend implementation:

`Route → validated params/search → access policy → loader/service → typed repository → runtime validation → fixture / Django adapter → UI`

But mutable/private/business-significant truth remains backend-authoritative.

Web authentication truth: Django Session + CSRF + OTP. No localStorage/sessionStorage bearer token.

For unsafe planned endpoints, frontend consumes P01 CSRF bootstrap and sends `credentials: include` plus `X-CSRFToken`.

Cross-repo runtime status remains:

`FRONTEND MOCK / BACKEND PENDING`

until an owning domain endpoint is implemented, permission-tested and merged under backend phase protocol.

## 5. Cross-repo alignment history

### F03 — My Tournaments
- planned `GET /api/v1/me/tournaments/`;
- backend PR #10 merged; runtime pending.

### F04 — My Matches
- planned `GET /api/v1/me/matches/`;
- backend Issue #11 completed; PR #12 merged; runtime pending.

### F05 — Result Submission
- planned `GET/POST /api/v1/matches/{matchId}/result/`;
- backend Issue #13 completed; PR #14 merged; runtime pending.

### F06 — Match Dispute
- backend Issue #15 completed; PR #16 merged; runtime pending.

### F10 — Player Notifications Inbox
- backend Issue #17 completed; PR #18 merged; runtime pending.

### F11 — Player Settings & Notification Preferences
- backend Issue #19 completed; PR #20 merged;
- planned `GET/PATCH /api/v1/me/settings/notification-preferences/`;
- runtime pending.

### F12 — Player Rivalries Hub
- backend Issue #21 completed; PR #22 merged;
- planned `GET /api/v1/me/rivalries/`;
- backend/repository owns rivalry membership/identity/finalized-valid head-to-head/latest encounter/filter/sort/summary/pagination truth;
- runtime pending.

### F13 — Player Achievements Hub (active docs alignment)

Contract source: `docs/F13_PLAYER_ACHIEVEMENTS_CONTRACT.md`.

Planned endpoint:
- `GET /api/v1/me/achievements/`.

Permanent decisions:
- private authenticated current-player projection;
- server owns achievement definitions, stable IDs/codes, categories, status, progress when present, unlock timestamp, summary, filters, ordering and pagination;
- frontend MUST NOT derive unlock eligibility/status from Match/Tournament/Challenge history;
- no XP economy, financial reward, trophy grade/rarity, social comparison, claim/mutation flow or Achievement Detail route is introduced;
- no Challenge unlock/rating inference is introduced;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F13 backend alignment:
1. keep diff documentation-only: `PROJECT_CONTINUITY.md` + `docs/F13_PLAYER_ACHIEVEMENTS_CONTRACT.md`;
2. do not modify Python, migrations, models, serializers, views, URLs, dependencies or `docs/PHASE_REGISTRY.md`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR and require green CI + review threads 0;
5. verify pre-merge backend main exact START_SHA;
6. merge with expected-head lock;
7. require post-merge backend main Quality Gate;
8. record terminal docs-alignment evidence in Issue #23 and close completed;
9. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F13 independently continues its implementation/QA/PR/closeout chain. Completion of Issue #23 is contract alignment only and MUST NOT be described as live Achievements backend implementation.
