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

Current accepted backend main / F11 docs-alignment base:

`e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`

That main contains P00/P01 plus completed F03/F04/F05/F06/F10 cross-repo contract documentation. It does **not** contain tournaments/matches/results/disputes/notifications/settings-preferences domain implementation.

F10 documentation alignment is terminally complete:
- Issue `#17` — CLOSED / COMPLETED;
- docs head `6e452ea74ec91d4c402f282a173384ce27744fde`;
- PR `#18` — MERGED;
- accepted backend main `e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`;
- post-main Backend Quality Gate `34469522243` — PASS on Python 3.12 and 3.14;
- runtime still `FRONTEND MOCK / BACKEND PENDING` for notification implementation.

Active backend workstream:

- `Cross-repo F11 — Player Settings notification-preferences contract alignment`;
- status: `IN PROGRESS — DOCUMENTATION ONLY`;
- START_SHA: `e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`;
- branch: `docs/f11-player-settings-contract`;
- Issue: `#19`;
- contract: `docs/F11_PLAYER_SETTINGS_CONTRACT.md`;
- Python/models/migrations/URLs/phase-registry mutation: `FORBIDDEN / NONE`.

Frontend F11 baseline:

`4e3a347de9140636bc95e37b096f67f146ed2e70` — F10 terminal frozen main

Frontend F10 terminal evidence:
- Issue `sajadkhavas/turnoment#59` — CLOSED / COMPLETED;
- terminal Quality Gate `34474656269` — PASS;
- terminal artifact `10151074107`;
- route `/dashboard/notifications` frozen `FINAL_PRIVATE`;
- runtime notification backend remains pending.

Frontend F11:
- route `/dashboard/settings`;
- START_SHA `4e3a347de9140636bc95e37b096f67f146ed2e70`;
- branch `phase/f11-player-settings`;
- Issue `sajadkhavas/turnoment#62`;
- target `FINAL_PRIVATE`;
- runtime settings persistence remains `FRONTEND MOCK / BACKEND PENDING` until an owning backend implementation exists.

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`;
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`;
- Backend NEXT → `P02 — Games / Catalog Foundation`.

F03/F04/F05/F06/F10/F11 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as runtime implementation of tournaments/matches/results/disputes/notifications/settings.

## 4. Permanent product/auth law

Frontend architecture may finalize ahead of backend implementation:

`Route → validated params/search → access policy → loader/service → typed repository → runtime validation → fixture / Django adapter → UI`

But mutable/private truth remains backend-authoritative.

Web authentication truth: Django Session + CSRF + OTP. No localStorage/sessionStorage bearer token.

For an unsafe planned endpoint, frontend consumes P01 CSRF bootstrap and sends `credentials: include` plus `X-CSRFToken`.

Cross-repo runtime status remains:

`FRONTEND MOCK / BACKEND PENDING`

until the owning domain endpoint is implemented, permission-tested and merged under backend phase protocol.

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
- backend owner `results`;
- Issue #13 completed;
- PR #14 merged;
- accepted backend main `93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`;
- PR CI `34394337599` PASS;
- post-merge CI `34394628782` PASS;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F06 — Match Dispute
- status `DONE — DOCUMENTATION / CROSS-REPO ALIGNMENT CLOSED`;
- backend Issue #15 completed;
- PR #16 merged;
- accepted main `38dccbf213d5f439e56cd608e3e4ac419d5092d1`;
- PR CI `34409560819` PASS Python 3.12/3.14;
- post-merge CI `34409893478` PASS Python 3.12/3.14;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F10 — Player Notifications Inbox
- status `DONE — DOCUMENTATION / CROSS-REPO ALIGNMENT CLOSED`;
- backend Issue #17 completed;
- PR #18 merged;
- accepted main `e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`;
- post-main CI `34469522243` PASS Python 3.12/3.14;
- planned endpoints under `docs/F10_NOTIFICATIONS_CONTRACT.md`;
- Python/models/migrations/URL implementation NONE;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F11 — Player Settings & Notification Preferences (active docs alignment)

Contract source: `docs/F11_PLAYER_SETTINGS_CONTRACT.md`.

Planned endpoints:
- `GET /api/v1/me/settings/notification-preferences/`;
- `PATCH /api/v1/me/settings/notification-preferences/`.

Permanent decisions:
- private authenticated current-player ownership;
- Django Session + CSRF for mutation;
- optional categories exactly `tournament`, `match`, `challenge`;
- mandatory `account` and `system` notices remain enabled;
- backend-owned persisted defaults and opaque revision;
- stale writes fail closed and return authoritative current settings;
- preference changes are prospective and do not delete existing inbox items;
- preferences never mutate competitive/business truth;
- no PWA/web-push subscription flow is implied or implemented;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F11 backend alignment:
1. keep diff documentation-only (`PROJECT_CONTINUITY.md` + `docs/F11_PLAYER_SETTINGS_CONTRACT.md`);
2. do not modify Python, migrations, models, URLs, dependencies or `docs/PHASE_REGISTRY.md`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR and require green CI + review threads 0;
5. verify pre-merge backend main exact START_SHA;
6. merge with expected-head lock;
7. require post-merge backend main Quality Gate;
8. record terminal docs-alignment evidence in Issue #19 and close completed;
9. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F11 independently continues its implementation/QA/PR/closeout chain. Completion of Issue #19 is contract alignment only and MUST NOT be described as live Settings backend implementation.
