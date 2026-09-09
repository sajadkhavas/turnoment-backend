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

Accepted backend main before active F06 docs alignment:

`93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`

That main contains P00/P01 plus F03/F04/F05 cross-repo documentation alignment. It does **not** contain matches/results/disputes domain implementation.

Active backend workstream:

- `Cross-repo F06 — Match Dispute contract alignment`
- status: `IN PROGRESS — DOCUMENTATION ONLY`
- START_SHA: `93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`
- branch: `docs/f06-dispute-contract`
- Issue: `#15`
- exact contract: `docs/F06_DISPUTE_CONTRACT.md`
- Python/models/migrations/phase-registry mutation: `FORBIDDEN / NONE`

Frontend terminal baseline before F06:

`0407a925974d50b4a75af292231bacb48c66eb38`

Frontend terminal F05 Quality Gate:

`34407220433` — PASS

Active frontend workstream:

- `F06 — Match Dispute`
- route `/matches/$id/dispute`
- START_SHA `0407a925974d50b4a75af292231bacb48c66eb38`
- branch `phase/f06-dispute`
- Issue `sajadkhavas/turnoment#47`

## 3. Backend phase state

- P00 — Backend Foundation & Frontend Contract Baseline → `DONE / MERGED / FROZEN`
- P01 — Accounts, Player Identity & Authentication Foundation → `DONE / MERGED / FROZEN`
- Backend NEXT → `P02 — Games / Catalog Foundation`

F03/F04/F05/F06 cross-repo alignment is governance/documentation only and MUST NOT be represented as P02 or as implementation of tournaments/matches/results/disputes.

## 4. Permanent product/auth law

Frontend architecture may finalize ahead of backend implementation:

`Route → validated params/search → access policy → loader/service → typed repository → runtime validation → fixture / Django adapter → UI`

But mutable competitive truth remains backend-authoritative.

Web authentication truth: Django Session + CSRF + OTP. No localStorage bearer token.

Cross-repo runtime status remains:

`FRONTEND MOCK / BACKEND PENDING`

until the owning domain endpoint is implemented, permission-tested and merged under backend phase protocol.

## 5. Cross-repo alignment history

### F03 — My Tournaments
- frontend `/dashboard/tournaments`
- planned `GET /api/v1/me/tournaments/`
- backend PR #10 merged
- accepted main `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- post-merge CI `34380281593` PASS

### F04 — My Matches
- frontend `/dashboard/matches`
- planned `GET /api/v1/me/matches/`
- backend Issue #11 completed
- PR #12 merged
- accepted main `baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`
- post-merge CI `34388924185` PASS on Python 3.12/3.14

### F05 — Result Submission
- frontend `/matches/$id/result`
- planned `GET/POST /api/v1/matches/{matchId}/result/`
- backend owner `results`
- backend Issue #13 completed
- backend PR #14 merged
- docs head `4e1826d7be562e3cecef3d61070fe7ab8baa2379`
- accepted backend main `93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`
- PR CI `34394337599` PASS Python 3.12/3.14
- post-merge CI `34394628782` PASS Python 3.12/3.14
- Python/models/migrations/phase-order implementation: NONE
- runtime `FRONTEND MOCK / BACKEND PENDING`

### F06 — Match Dispute (active docs alignment)

Backend owner: `disputes`

Planned endpoints:
- `GET /api/v1/matches/{matchId}/dispute/`
- `POST /api/v1/matches/{matchId}/dispute/`
- `POST /api/v1/matches/{matchId}/dispute/{disputeId}/evidence/`

Contract source: `docs/F06_DISPUTE_CONTRACT.md`

Permanent decisions:
- Django Session + server-side Match/participant/dispute authorization;
- CSRF on create/evidence;
- opaque revision/stale semantics;
- Idempotency-Key for logical create/evidence attempts;
- backend-owned eligibility, lifecycle, moderation decision and result/rating effects;
- private evidence upload with server-side file type/signature/count/size/storage/security validation;
- browser MIME is convenience only;
- no dispute withdrawal command invented by frontend;
- runtime remains `FRONTEND MOCK / BACKEND PENDING`.

## 6. Exact NEXT

Active F06 backend alignment:
1. confirm branch diff is documentation-only;
2. run Backend Quality Gate on Python 3.12 and 3.14;
3. open docs PR and require green CI + review threads 0;
4. merge with exact-head lock;
5. require post-merge backend main Quality Gate;
6. record terminal evidence in Issue #15 and close completed;
7. Backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend F06 independently continues its implementation/QA/PR/closeout chain.
