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

Current accepted backend main / F12 docs-alignment base:

`3fb421cf2c85d94753ddf9352d8bc1134358847a`

That main contains P00/P01 plus completed F03/F04/F05/F06/F10/F11 cross-repo contract documentation. It does **not** contain tournaments/matches/results/disputes/notifications/settings/rivalries runtime domain implementation.

F11 documentation alignment is terminally complete:
- Issue `#19` — CLOSED / COMPLETED;
- docs head `44aee41fac159d5095218af06b635e9caa519375`;
- PR `#20` — MERGED;
- accepted backend main `3fb421cf2c85d94753ddf9352d8bc1134358847a`;
- post-main Backend Quality Gate `34477753302` — PASS on Python 3.12 and 3.14;
- runtime remains `FRONTEND MOCK / BACKEND PENDING` for Settings persistence.

Active backend workstream:
- `Cross-repo F12 — Player Rivalries Hub contract alignment`;
- status: `IN PROGRESS — DOCUMENTATION ONLY`;
- START_SHA: `3fb421cf2c85d94753ddf9352d8bc1134358847a`;
- branch: `docs/f12-player-rivalries-contract`;
- Issue: `#21`;
- contract: `docs/F12_PLAYER_RIVALRIES_CONTRACT.md`;
- Python/models/migrations/serializers/views/URLs/dependencies/phase-registry mutation: `FORBIDDEN / NONE`.

Frontend F12:
- repo `sajadkhavas/turnoment`;
- route `/dashboard/rivalries`;
- frontend START_SHA `47ea1ed9bda2a788860f382bc75ea50a83efaaf3` — F11 terminal frozen main;
- branch `phase/f12-player-rivalries`;
- Issue `sajadkhavas/turnoment#65`;
- target `FINAL_PRIVATE`;
- runtime rivalries endpoint remains `FRONTEND MOCK / BACKEND PENDING` until an owning backend phase implements it.

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`;
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`;
- Backend NEXT → `P02 — Games / Catalog Foundation`.

F03/F04/F05/F06/F10/F11/F12 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as live runtime implementation.

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
- frontend `/dashboard/tournaments`;
- planned `GET /api/v1/me/tournaments/`;
- backend PR #10 merged;
- accepted main `cd47fff8b82359b12d86fad10735a2e9fa52472d`;
- post-merge CI `34380281593` PASS.

### F04 — My Matches
- frontend `/dashboard/matches`;
- planned `GET /api/v1/me/matches/`;
- backend Issue #11 completed;
- PR #12 merged;
- accepted main `baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`;
- post-merge CI `34388924185` PASS Python 3.12/3.14.

### F05 — Result Submission
- frontend `/matches/$id/result`;
- planned `GET/POST /api/v1/matches/{matchId}/result/`;
- backend Issue #13 completed;
- PR #14 merged;
- accepted main `93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`;
- post-merge CI `34394628782` PASS;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F06 — Match Dispute
- backend Issue #15 completed;
- PR #16 merged;
- accepted main `38dccbf213d5f439e56cd608e3e4ac419d5092d1`;
- post-main CI `34409893478` PASS Python 3.12/3.14;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F10 — Player Notifications Inbox
- backend Issue #17 completed;
- PR #18 merged;
- accepted main `e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`;
- post-main CI `34469522243` PASS Python 3.12/3.14;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F11 — Player Settings & Notification Preferences
- backend Issue #19 completed;
- PR #20 merged;
- accepted main `3fb421cf2c85d94753ddf9352d8bc1134358847a`;
- post-main CI `34477753302` PASS Python 3.12/3.14;
- planned `GET/PATCH /api/v1/me/settings/notification-preferences/`;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F12 — Player Rivalries Hub (active docs alignment)

Contract source: `docs/F12_PLAYER_RIVALRIES_CONTRACT.md`.

Planned endpoint:
- `GET /api/v1/me/rivalries/`.

Permanent decisions:
- private authenticated current-player projection;
- one server-defined rivalry row per current-player/opponent/game relationship;
- server owns rivalry membership, IDs, finalized-valid head-to-head aggregates, latest finalized encounter, filters, sort, summary and pagination;
- only finalized valid non-void encounters contribute;
- no Challenge unlock/rating inference;
- no wager/stake mechanics;
- no friend/block/social graph behavior;
- no Rivalry Detail route or mutation is introduced by F12;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F12 backend alignment:
1. keep diff documentation-only: `PROJECT_CONTINUITY.md` + `docs/F12_PLAYER_RIVALRIES_CONTRACT.md`;
2. do not modify Python, migrations, models, serializers, views, URLs, dependencies or `docs/PHASE_REGISTRY.md`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR and require green CI + review threads 0;
5. verify pre-merge backend main exact START_SHA;
6. merge with expected-head lock;
7. require post-merge backend main Quality Gate;
8. record terminal docs-alignment evidence in Issue #21 and close completed;
9. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F12 independently continues its implementation/QA/PR/closeout chain. Completion of Issue #21 is contract alignment only and MUST NOT be described as live Rivalries backend implementation.
