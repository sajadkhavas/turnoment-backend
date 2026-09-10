# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-11`

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

Current accepted backend main / F14 docs-alignment START_SHA:

`ddfdceaa9746cc6a60ad2b5e18e630c53904f00c`

That SHA contains P00/P01 plus completed F03/F04/F05/F06/F10/F11/F12/F13 cross-repo contract documentation. It does **not** contain tournaments/matches/results/disputes/notifications/settings/rivalries/achievements/teams runtime domain implementation.

F13 documentation alignment is terminally complete:
- Issue `#23` — CLOSED / COMPLETED;
- docs head `f6d54a77370b268f1d240180d5eacda86d100dd8`;
- PR `#24` — MERGED;
- PR Quality Gate `34521995236` — PASS on Python 3.12 and 3.14;
- accepted backend main `ddfdceaa9746cc6a60ad2b5e18e630c53904f00c`;
- post-main Backend Quality Gate `34522798713` — PASS on Python 3.12 and 3.14;
- runtime remains `FRONTEND MOCK / BACKEND PENDING` for Achievements.

Active backend workstream:
- `Cross-repo F14 — Player Teams Hub contract alignment`;
- status: `IN PROGRESS — DOCUMENTATION ONLY`;
- START_SHA: `ddfdceaa9746cc6a60ad2b5e18e630c53904f00c`;
- branch: `docs/f14-player-teams-contract`;
- Issue: `#25`;
- contract: `docs/F14_PLAYER_TEAMS_CONTRACT.md`;
- Python/models/migrations/serializers/views/URLs/dependencies/phase-registry mutation: `FORBIDDEN / NONE`.

Frontend F14:
- repo `sajadkhavas/turnoment`;
- route `/dashboard/teams`;
- frontend START_SHA `80d367fbf9da858a2c1cfb64df4714f136ff2c4c` — F13 terminal frozen main;
- branch `phase/f14-player-teams`;
- Issue `sajadkhavas/turnoment#71`;
- target `FINAL_PRIVATE`;
- runtime Teams endpoint remains `FRONTEND MOCK / BACKEND PENDING` until an owning backend phase implements it.

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`;
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`;
- Backend NEXT → `P02 — Games / Catalog Foundation`.

F03/F04/F05/F06/F10/F11/F12/F13/F14 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as live runtime implementation.

## 4. Permanent product/auth law

Frontend architecture may finalize ahead of backend implementation:

`Route → validated params/search → access policy → loader/service → typed repository → runtime validation → fixture / Django adapter → UI`

But mutable/private/business-significant truth remains backend-authoritative.

Web authentication truth: Django Session + CSRF + OTP. No localStorage/sessionStorage bearer token.

For private reads, browser requests include session credentials. Unsafe future commands consume the P01 CSRF contract and send `credentials: include` plus `X-CSRFToken`.

Cross-repo runtime status remains:

`FRONTEND MOCK / BACKEND PENDING`

until an owning domain endpoint is implemented, permission-tested and merged under backend phase protocol.

## 5. Cross-repo alignment history

### F03 — My Tournaments
- planned `GET /api/v1/me/tournaments/`;
- team participation already uses stable `teamId`, `teamName` and role `captain | member`;
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
- runtime pending.

### F12 — Player Rivalries Hub
- backend Issue #21 completed; PR #22 merged;
- runtime pending.

### F13 — Player Achievements Hub
- backend Issue #23 completed; PR #24 merged;
- runtime pending.

### F14 — Player Teams Hub (active docs alignment)

Contract source: `docs/F14_PLAYER_TEAMS_CONTRACT.md`.

Planned endpoint:
- `GET /api/v1/me/teams/`.

Permanent decisions:
- private authenticated current-player projection;
- server owns team membership, stable team identity/name, current-player role, roster membership/roles, counts, selected-team resolution, summary and roster pagination;
- frontend MUST NOT reconstruct current membership/role from tournament participation history;
- F14 is read-only and declares no create/rename/delete/invite/kick/leave/captain-transfer mutation contract;
- no team rating/ranking, tournament/challenge eligibility inference, friend/social graph or Team Detail route is introduced;
- `/dashboard/challenges` remains isolated;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F14 backend alignment:
1. keep diff documentation-only: `PROJECT_CONTINUITY.md` + `docs/F14_PLAYER_TEAMS_CONTRACT.md`;
2. do not modify Python, migrations, models, serializers, views, URLs, dependencies or `docs/PHASE_REGISTRY.md`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR and require green CI + review threads 0;
5. verify pre-merge backend main exact START_SHA;
6. merge with expected-head lock;
7. require post-merge backend main Quality Gate;
8. record terminal docs-alignment evidence in Issue #25 and close completed;
9. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F14 independently continues its implementation/QA/PR/closeout chain. Completion of Issue #25 is contract alignment only and MUST NOT be described as live Teams backend implementation.
