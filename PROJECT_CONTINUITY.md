# TURNOMENT — PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**
>
> Operational source of truth for continuing the Turnoment backend without duplicate work.

Last checkpoint update: `2026-09-09`

## 1. Mandatory continuation protocol

Every chat/agent working on this project MUST:

1. Read this file before implementation.
2. Verify the current `main` SHA of every repository it will change.
3. Read relevant phase/PR/Issue evidence before repeating work.
4. Work on a dedicated branch unless doing a documented closeout branch.
5. Never mark work `DONE` from conversation memory alone.
6. Update continuity before ending, including partial/blocked/merge-ready work.
7. Record exact SHA / branch / PR / CI / test evidence when available.
8. If cross-repo API contracts or global project state change, update continuity in BOTH repositories.

Allowed operational statuses:
`PLANNED`, `IN PROGRESS`, `PARTIAL / SAFE CHECKPOINT`, `BLOCKED`, `READY TO MERGE`, `DONE / MERGED / FROZEN`.

## 2. Repository truth

### Frontend

Repository: `sajadkhavas/turnoment`

Latest terminal accepted frontend `main` before active F05:

`864fe1491739b06c763be487a73a589c7e0f3609`

Terminal frontend Quality Gate:

`34391019079` — PASS

Accepted relevant routes:
- F02 `/games/$slug` → `DONE / MERGED / FROZEN — FINAL_CURRENT`
- F03 `/dashboard/tournaments` → `DONE / MERGED / FROZEN — FINAL_PRIVATE`
- F04 `/dashboard/matches` → `DONE / MERGED / FROZEN — FINAL_PRIVATE`
- F04 terminal evidence: frontend Issue `#41`

Active frontend workstream:
- `F05 — Result Submission /matches/$id/result`
- status: `IN PROGRESS`
- START_SHA: `864fe1491739b06c763be487a73a589c7e0f3609`
- branch: `phase/f05-result-submission`
- frontend Issue: `sajadkhavas/turnoment#44`
- evidence: `docs/workstreams/F05_RESULT_SUBMISSION.md`
- runtime integration remains `FRONTEND MOCK / BACKEND PENDING`

### Backend

Repository: `sajadkhavas/turnoment-backend`

Verified backend `main` before F05 documentation alignment:

`baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`

That main includes the completed F03/F04 cross-repo documentation alignments and no matches/results/disputes domain implementation.

Active backend workstream:
- `F05 Result Submission cross-repo contract alignment`
- status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT ONLY`
- START_SHA: `baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`
- branch: `docs/f05-result-submission-contract`
- tracking Issue: `#13`
- scope: refine existing `results` owner into exact planned GET/POST Result Submission contract
- Python/models/migrations/phase-registry mutation: `FORBIDDEN / NONE`

## 3. Backend phase state

- `P00 — Backend Foundation & Frontend Contract Baseline` → `DONE / MERGED / FROZEN`
- `P01 — Accounts, Player Identity & Authentication Foundation` → `DONE / MERGED / FROZEN`
- Backend NEXT → `P02 — Games / Catalog Foundation`

Historical backend phase evidence remains authoritative in:
- `PHASE_COMPLETION_PROTOCOL.md`
- `docs/PHASE_REGISTRY.md`
- phase-specific GitHub Issues / PRs

F03/F04/F05 cross-repo documentation alignment is governance only. It MUST NOT be recorded as P02 or as backend implementation of tournaments, matches, results or disputes.

## 4. Product architecture law

Frontend is NOT the business source of truth.

Anything that is content, commercial data, competitive state, user state, configurable product data, operational status, SEO entity data, or an action that changes system truth must ultimately be backend-authoritative and available through an API contract.

Backend-authoritative examples include tournament lifecycle, registration/check-in, matches, result submission/confirmation, finalized score/outcome/rating delta, disputes, challenges/rivalries and payments.

Pure presentation such as layout, spacing, animation and design tokens remains frontend-owned.

## 5. Permanent frontend relationship

Accepted frontend architecture:

`Route → validated params/search → route access policy → loader/service → typed repository contract → runtime validation → Mock adapter / Django HTTP adapter → UI`

A frontend route may become final ahead of backend implementation, but cross-repo integration remains:

`FRONTEND MOCK / BACKEND PENDING`

until the owning backend domain/API is implemented, permission-tested and merged under the backend phase protocol.

Web authentication truth remains Django Session + CSRF + OTP. Do not introduce localStorage bearer auth.

## 6. Cross-repo API alignment

### F03 — My Tournaments
- frontend: `/dashboard/tournaments`
- backend owner: `registrations/tournaments`
- planned endpoint: `GET /api/v1/me/tournaments/`
- backend alignment PR #10 merged
- alignment main: `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- post-merge Quality Gate `34380281593` — PASS
- runtime: `FRONTEND MOCK / BACKEND PENDING`

### F04 — My Matches
- frontend: `/dashboard/matches`
- owners: `matches / results / disputes`
- planned endpoint: `GET /api/v1/me/matches/`
- backend alignment Issue #11 completed
- backend docs PR #12 merged
- alignment merge/main: `baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`
- post-merge Quality Gate `34388924185` — PASS on Python 3.12 and 3.14
- runtime: `FRONTEND MOCK / BACKEND PENDING`

### F05 — Result Submission

Frontend route:

`/matches/$id/result`

Backend owner:

`results`

Existing baseline had already reserved result submit/confirm ownership. F05 now refines Result Submission only into exact planned web endpoints:

`GET /api/v1/matches/{matchId}/result/`

`POST /api/v1/matches/{matchId}/result/`

Permanent decisions recorded in `docs/FRONTEND_BACKEND_CONTRACT.md`:
- Django Session authentication and server-side Match/participant authorization;
- CSRF-protected POST through the P01 CSRF bootstrap contract;
- opaque backend-generated `revision` for stale-state detection;
- authoritative `reportable | awaiting-confirmation | finalized | disputed | unavailable` projection;
- backend-owned score policy and validation;
- `Idempotency-Key` per logical submit attempt, with persistent/transaction-safe semantics required before implementation can be live;
- typed accepted/validation/stale/unavailable/already-submitted outcomes;
- frontend never derives winner/outcome/rating delta from submitted scores;
- confirmation and dispute remain separate later workstreams.

Current F05 integration status:

`FRONTEND MOCK / BACKEND PENDING`

No results/matches Python implementation is claimed by this alignment.

Cross-repo F05 documentation evidence:
- backend branch: `docs/f05-result-submission-contract`
- backend Issue: `#13`
- backend START_SHA: `baeffe042f4dc6ab6d2cbd0433eca4f8404daff6`
- frontend frozen START_SHA: `864fe1491739b06c763be487a73a589c7e0f3609`
- frontend branch: `phase/f05-result-submission`
- frontend Issue: `#44`
- Python code changed: `NO`
- models/migrations changed: `NO`
- `docs/PHASE_REGISTRY.md` changed: `NO`
- backend phase order changed: `NO`

## 7. Backend NEXT

### P02 — Games / Catalog Foundation

Status: `PLANNED`

P02 must start only through its own mandatory phase workflow from the then-current verified backend main.

Expected direction remains game identity/slug, publication/activation state, platform metadata, tournament-facing game configuration, public game catalog, frontend Game Listing/Detail API alignment, admin management, permissions, migrations/tests/CI/registry evidence.

F05 does not change this order.

## 8. Exact NEXT

For active backend F05 documentation alignment:
1. review diff and confirm only contract/continuity docs changed;
2. run Backend Quality Gate on Python 3.12 and 3.14;
3. open PR and require green CI + review threads 0;
4. merge documentation only;
5. require post-merge backend main Quality Gate;
6. record terminal alignment evidence in Issue #13 and close completed;
7. backend NEXT remains `P02 — Games / Catalog Foundation`.

Frontend independently continues F05 Result Submission through its own QA/PR/closeout chain.
