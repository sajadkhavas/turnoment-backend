# TURNOMENT — PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**
>
> This file is the current operational checkpoint for the whole Turnoment project. Read it before making changes and update it before ending a session.

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

- `PLANNED`
- `IN PROGRESS`
- `PARTIAL / SAFE CHECKPOINT`
- `BLOCKED`
- `READY TO MERGE`
- `DONE / MERGED / FROZEN`

## 2. Source-of-truth repositories

### Frontend

Repository: `sajadkhavas/turnoment`

Role: public/player/venue product UI and SSR frontend.

Latest terminal accepted frontend `main` before active F04:

`df7c4e8c6c60c35616bba1143814b5d2a7a408c7`

Latest terminal frontend Quality Gate:

`34386636373` — PASS

Accepted route truth relevant here:

- F02 `/games/$slug` → `DONE / MERGED / FROZEN — FINAL_CURRENT`
- F03 `/dashboard/tournaments` → `DONE / MERGED / FROZEN — FINAL_PRIVATE`
- F03 terminal evidence: frontend Issue `#38`

Active frontend workstream:

- `F04 — My Matches /dashboard/matches`
- status: `IN PROGRESS`
- START_SHA: `df7c4e8c6c60c35616bba1143814b5d2a7a408c7`
- branch: `phase/f04-my-matches`
- frontend Issue: `sajadkhavas/turnoment#41`
- evidence: `docs/workstreams/F04_MY_MATCHES.md`

### Backend

Repository: `sajadkhavas/turnoment-backend`

Role: domain/data/business-logic source of truth and API.

Stack:

- Python
- Django 6.1
- Django REST Framework
- PostgreSQL
- Redis
- Celery

Verified backend `main` before this documentation alignment:

`cd47fff8b82359b12d86fad10735a2e9fa52472d`

That main includes the completed F03 cross-repo documentation alignment. It did not implement tournaments/registrations code.

Active F04 documentation-only cross-repo alignment:

- status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT ONLY`
- START_SHA: `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- branch: `docs/f04-my-matches-contract`
- tracking Issue: `#11`
- scope: add the planned authenticated My Matches projection and refresh continuity only
- Python/models/migrations/phase-registry mutation: `FORBIDDEN / NONE`

## 3. Backend phase state

- `P00 — Backend Foundation & Frontend Contract Baseline` → `DONE / MERGED / FROZEN`
- `P01 — Accounts, Player Identity & Authentication Foundation` → `DONE / MERGED / FROZEN`
- Backend NEXT → `P02 — Games / Catalog Foundation`

Historical backend phase evidence remains authoritative in:

- `PHASE_COMPLETION_PROTOCOL.md`
- `docs/PHASE_REGISTRY.md`
- phase-specific GitHub Issues / PRs

F03/F04 cross-repo documentation alignment is governance only. It MUST NOT be recorded as P02 or as implementation of tournaments, matches, results or disputes.

## 4. Product architecture law

Frontend is NOT the business source of truth.

Anything that is content, commercial data, competitive state, user state, configurable product data, operational status, SEO entity data, or an action that changes system truth must ultimately be backend-authoritative and available through an API contract.

Frontend-owned examples:

- spacing
- layout
- visual effects
- animation
- design tokens

Backend-authoritative examples:

- tournaments / registrations
- games / gaming centers
- players / rankings
- match lifecycle/results/rating deltas
- result submission/confirmation
- disputes
- challenges / rivalries
- notifications
- payments/refunds/settlements

## 5. Current frontend production rule

Pages are built as the FINAL frontend architecture, not temporary screens requiring later router/SSR/contract reconstruction.

Target flow:

`Route → validated params/search → route access policy → loader/service → typed repository contract → runtime validation → Mock adapter / Django HTTP adapter → UI`

A frontend surface may be accepted ahead of its backend implementation, but cross-repo integration remains explicitly:

`FRONTEND MOCK / BACKEND PENDING`

until the owning backend domain/API is implemented and tested.

Current relevant frontend truth:

- `/dashboard` is final private and uses P01 Django Session truth.
- `/games/$slug` is frontend `FINAL_CURRENT`; backend Games/Catalog is still P02.
- `/dashboard/tournaments` is frontend `FINAL_PRIVATE`; backend `registrations/tournaments` is pending its accepted phase order.
- `/dashboard/matches` is active F04 and is being rebuilt on a permanent typed/runtime-validated contract.

## 6. Backend NEXT

### P02 — Games / Catalog Foundation

Status: `PLANNED`

P02 must start only through its own mandatory phase workflow from the then-current verified backend main.

Expected direction remains:

- game identity / slug
- publication/activation state
- platform support metadata
- tournament-facing game configuration boundary
- public game catalog
- frontend Game Listing / Game Detail API alignment
- admin management
- permissions
- migrations/tests/CI/registry evidence

Neither F03 nor F04 changes this order.

## 7. Cross-repo API alignment

Backend changes that alter API shape/business semantics must update frontend expectations. Frontend changes that introduce backend-authoritative data must be mapped to backend owner/domain/API before product integration is considered complete.

### F03 — My Tournaments

- frontend: `/dashboard/tournaments`
- backend owner: `registrations/tournaments`
- planned endpoint: `GET /api/v1/me/tournaments/`
- backend alignment PR #10 → MERGED
- alignment main: `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- backend post-merge Quality Gate: `34380281593` — PASS
- runtime status: `FRONTEND MOCK / BACKEND PENDING`

### F04 — My Matches

Existing baseline already owned:

- `/matches/{id}` → `matches`
- result submission/confirmation → `results`
- disputes/evidence → `disputes`

F04 adds the missing authenticated player-list projection:

`GET /api/v1/me/matches/`

Backend owners:

- `matches` for list membership, lifecycle, schedule, opponent/competition/venue and check-in truth;
- `results` for report/confirmation/finalized score/outcome/rating-delta projection;
- `disputes` for active/review/resolved dispute truth.

Planned URL query:

- state: `upcoming | action-required | completed | disputed`
- kind: `tournament | challenge`
- game: stable game ID
- page: positive integer

Permanent response projection and enum/integrity rules are recorded in `docs/FRONTEND_BACKEND_CONTRACT.md`.

F04 list UI does not implement Result Submission or Dispute mutations; those remain dedicated future frontend workstreams and dedicated backend owners.

Current integration status:

`FRONTEND MOCK / BACKEND PENDING`

No F04 backend domain/API implementation is claimed by this documentation alignment.

Cross-repo F04 documentation evidence:

- branch: `docs/f04-my-matches-contract`
- Issue: `#11`
- backend START_SHA: `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- frontend START_SHA: `df7c4e8c6c60c35616bba1143814b5d2a7a408c7`
- frontend Issue: `sajadkhavas/turnoment#41`
- Python code changed: `NO`
- models/migrations changed: `NO`
- backend phase registry changed: `NO`
- backend phase order changed: `NO`

## 8. Exact NEXT

Backend NEXT remains:

`P02 — Games / Catalog Foundation`

Frontend NEXT independently:

`Complete active F04 — My Matches /dashboard/matches`, then proceed to the separately governed Result Submission workstream.

## 9. Latest session checkpoint

- Date: `2026-09-09`
- Repo changed: `turnoment-backend` documentation only
- Workstream: `F04 cross-repo My Matches contract alignment`
- Status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT ONLY`
- Backend START_SHA: `cd47fff8b82359b12d86fad10735a2e9fa52472d`
- Backend branch: `docs/f04-my-matches-contract`
- Backend Issue: `#11`
- Frontend frozen baseline: `df7c4e8c6c60c35616bba1143814b5d2a7a408c7`
- Frontend active F04 branch: `phase/f04-my-matches`
- Frontend Issue: `#41`
- Cross-repo state: `FRONTEND MOCK / BACKEND PENDING`
- Backend implementation/migrations: `NONE`
- Backend NEXT remains: `P02 — Games / Catalog Foundation`
- Exact NEXT for this documentation checkpoint: review diff, run backend CI, merge only if green; do not claim a backend phase completion.
