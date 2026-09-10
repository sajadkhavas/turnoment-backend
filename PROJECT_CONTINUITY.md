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

Accepted backend main before F10 documentation alignment:

`38dccbf213d5f439e56cd608e3e4ac419d5092d1`

That main contains P00/P01 plus completed F03/F04/F05/F06 cross-repo contract documentation. It does **not** contain tournaments/matches/results/disputes/notifications domain implementation.

Active backend workstream:

- `Cross-repo F10 — Player Notifications contract alignment`
- status: `IN PROGRESS — DOCUMENTATION ONLY`
- START_SHA: `38dccbf213d5f439e56cd608e3e4ac419d5092d1`
- branch: `docs/f10-player-notifications-contract`
- Issue: `#17`
- contract: `docs/F10_NOTIFICATIONS_CONTRACT.md`
- Python/models/migrations/phase-registry mutation: `FORBIDDEN / NONE`

Frontend F10 baseline:

`34d6a576691532e4228b2eecc0fea1c1d296d58e` — F09 terminal frozen main

Frontend F09 terminal Quality Gate:

`34468048698` — PASS

Frontend F10:
- route `/dashboard/notifications`;
- START_SHA `34d6a576691532e4228b2eecc0fea1c1d296d58e`;
- branch `phase/f10-player-notifications`;
- Issue `sajadkhavas/turnoment#59`;
- runtime remains `FRONTEND MOCK / BACKEND PENDING` until notification backend implementation exists.

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`;
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`;
- Backend NEXT → `P02 — Games / Catalog Foundation`.

F03/F04/F05/F06/F10 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as runtime implementation of tournaments/matches/results/disputes/notifications.

## 4. Permanent product/auth law

Frontend architecture may finalize ahead of backend implementation:

`Route → validated params/search → access policy → loader/service → typed repository → runtime validation → fixture / Django adapter → UI`

But mutable/private competitive truth remains backend-authoritative.

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
- merge/current accepted baseline `38dccbf213d5f439e56cd608e3e4ac419d5092d1`;
- PR CI `34409560819` PASS Python 3.12/3.14;
- post-merge CI `34409893478` PASS Python 3.12/3.14;
- Python/models/migrations/phase-registry mutation NONE;
- runtime `FRONTEND MOCK / BACKEND PENDING`.

### F10 — Player Notifications Inbox (active docs alignment)

Contract source: `docs/F10_NOTIFICATIONS_CONTRACT.md`.

Planned endpoints:
- `GET /api/v1/me/notifications/`;
- `POST /api/v1/me/notifications/{notificationId}/read/`;
- `POST /api/v1/me/notifications/read-all/`.

Permanent decisions:
- private authenticated current-player scope;
- Django Session + server-side authorization;
- CSRF on read-state commands;
- backend-owned recipient membership, notification identity/kind/content/time/read state, summary, ordering, pagination and navigation-target projection;
- list filters: `state=unread|read`, `kind=tournament|match|challenge|account|system`, `page`;
- mark-one and mark-all are idempotent domain transitions;
- notification targets are typed discriminated app targets, never arbitrary hrefs;
- F10 target kinds are restricted to already-existing/accepted routes; no Challenge Detail URL is invented;
- no push preference/delivery-settings contract is implied;
- frontend never infers competitive truth from notification content;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F10 backend alignment:
1. keep diff documentation-only (`PROJECT_CONTINUITY.md` + `docs/F10_NOTIFICATIONS_CONTRACT.md`);
2. do not modify Python, migrations, models, URLs or `docs/PHASE_REGISTRY.md`;
3. run Backend Quality Gate on Python 3.12 and 3.14;
4. open docs PR and require green CI + review threads 0;
5. verify pre-merge backend main exact START_SHA;
6. merge with expected-head lock;
7. require post-merge backend main Quality Gate;
8. record terminal docs-alignment evidence in Issue #17 and close completed;
9. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F10 independently continues its implementation/QA/PR/closeout chain. Completion of Issue #17 is contract alignment only and MUST NOT be described as live notification backend implementation.
