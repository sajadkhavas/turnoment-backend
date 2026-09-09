# TURNOMENT — PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**
>
> This file is the current operational checkpoint for the whole Turnoment project. Read it before making changes. Update it before ending the session — even when the work is incomplete, blocked, or only partially implemented.

Last checkpoint update: `2026-09-09`

## 1. Mandatory continuation protocol

Every chat/agent working on this project MUST:

1. Read this file before implementation.
2. Verify the recorded `main` SHA of the repository it will change.
3. Read the relevant phase/PR/Issue evidence before repeating work.
4. Work on a dedicated branch unless explicitly doing a documented closeout branch.
5. Never mark work `DONE` from conversation memory alone.
6. Before ending the session, update this file with the real current state, even if the task is unfinished.
7. Record exact SHA / branch / PR / CI / test evidence when available.
8. If cross-repo API contracts or global project state changed, update this file in BOTH repositories.

Allowed operational statuses:

- `PLANNED`
- `IN PROGRESS`
- `PARTIAL / SAFE CHECKPOINT`
- `BLOCKED`
- `READY TO MERGE`
- `DONE / MERGED / FROZEN`

A session MUST NOT use `DONE / MERGED / FROZEN` unless the required implementation is merged and its required final gates are green.

## 2. Source-of-truth repositories

### Frontend

Repository: `sajadkhavas/turnoment`

Role: public/player/venue product UI and SSR frontend.

Latest accepted `main` before active F03:

`4afb49e913d5fd7e2420031ae957fde2e79e3e8a`

Latest accepted frontend terminal gate:

- F02 `/games/$slug` → `DONE / MERGED / FROZEN — FINAL_CURRENT`
- terminal main Quality Gate: `34374298544` — PASS

Active frontend workstream:

- `F03 — My Tournaments /dashboard/tournaments`
- status: `IN PROGRESS`
- START_SHA: `4afb49e913d5fd7e2420031ae957fde2e79e3e8a`
- branch: `phase/f03-my-tournaments`
- frontend Issue: `sajadkhavas/turnoment#38`
- frontend draft PR: `sajadkhavas/turnoment#39`
- frontend workstream evidence: `docs/workstreams/F03_MY_TOURNAMENTS.md`

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

Current verified backend `main` SHA before this documentation alignment:

`b92213436c5acbc8cb40ce22d2d6e7dbe2b82f86`

Active documentation-only cross-repo alignment:

- status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT ONLY`
- branch: `docs/f03-my-tournaments-contract`
- tracking Issue: `#9`
- START_SHA: `b92213436c5acbc8cb40ce22d2d6e7dbe2b82f86`
- this is NOT a backend domain phase and does not replace/reorder P02.

## 3. Backend phase state

- `P00 — Backend Foundation & Frontend Contract Baseline` → `DONE / MERGED / FROZEN`
- `P01 — Accounts, Player Identity & Authentication Foundation` → `DONE / MERGED / FROZEN`
- Next backend phase: `P02 — Games / Catalog Foundation`

Historical backend phase evidence remains authoritative in:

- `PHASE_COMPLETION_PROTOCOL.md`
- `docs/PHASE_REGISTRY.md`
- phase-specific GitHub Issues / PRs

The F03 contract-alignment branch is documentation governance only. It MUST NOT be recorded as P02/P03 or as implementation of tournaments/registrations.

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

- tournaments
- games
- gaming centers
- players
- rankings
- registrations
- match state/results
- challenges
- rivalries
- stories/content
- notifications
- payments/refunds/settlements
- configurable SEO entity metadata

## 5. Current frontend production rule

Pages must be built as the FINAL frontend architecture, not temporary mock-only screens that require a later SSR/router/SEO reconstruction phase.

Target flow:

`Route → validated params/search → route access policy → loader/service → typed repository contract → runtime validation → Mock adapter / Django HTTP adapter → UI`

A UI screen may be designed and finalized on the frontend ahead of its backend domain implementation, but cross-repo product integration remains explicitly:

`FRONTEND MOCK / BACKEND PENDING`

until the backend contract/domain is implemented and tested.

Current accepted/active frontend truth relevant to backend ownership:

- `/dashboard` has a final private frontend architecture and reuses P01 Django Session authentication truth.
- `/games/$slug` is frontend `FINAL_CURRENT`; backend Games/Catalog remains owned by P02.
- `/dashboard/tournaments` is active F03 and uses a permanent repository/runtime-schema boundary; its backend owner remains `registrations/tournaments`.
- legacy ecommerce routes still exist and are not Turnoment competitive architecture references.

## 6. Backend NEXT

### P02 — Games / Catalog Foundation

Status: `PLANNED`

START_SHA must be locked from the actual backend `main` when P02 is explicitly begun; do not reuse stale historical SHA values without verification.

Expected direction:

- game identity / slug
- game publication/activation state
- platform support metadata
- tournament-facing game configuration boundary
- backend-authoritative public game catalog
- API contract aligned with frontend Game Listing / Game Detail
- admin management
- permissions
- tests / migrations / CI / registry evidence

Do not invent publisher/legal rule content as hardcoded truth; game-specific policy/rules should remain versionable/configurable.

F03 does not change this order. Tournaments/registrations backend implementation follows the accepted domain phase sequence after its prerequisite domains.

## 7. Cross-repo API alignment

Backend changes that alter API shape or business semantics must update the recorded frontend contract expectations.

Frontend changes that introduce new backend-authoritative data must be mapped to a backend owner/domain/API before the corresponding frontend product integration is considered complete.

If a session changes this cross-repo contract, update `PROJECT_CONTINUITY.md` in BOTH repositories.

### F03 — My Tournaments alignment

Existing approved ownership in `docs/FRONTEND_BACKEND_CONTRACT.md`:

- frontend surface: `/dashboard/tournaments`
- backend owner: `registrations/tournaments`
- planned endpoint: `GET /api/v1/me/tournaments/`

F03 refines that planned projection with URL-query state/game/page filters and backend-authoritative lifecycle, registration, check-in, participation, result, summary, pagination and next-action fields.

Current integration status:

`FRONTEND MOCK / BACKEND PENDING`

The active frontend branch includes the permanent Django HTTP adapter mapping, but the API/domain is not to be described as live integration until the owning backend tournaments/registrations phase implements, permission-tests, merges and closes it under the mandatory backend phase protocol.

Cross-repo documentation alignment evidence:

- backend branch: `docs/f03-my-tournaments-contract`
- backend Issue: `#9`
- contract file: `docs/FRONTEND_BACKEND_CONTRACT.md`
- backend code/migrations changed by this checkpoint: `NO`
- backend phase order changed: `NO`

## 8. Exact NEXT

Backend NEXT remains:

`P02 — Games / Catalog Foundation`, started only through its own mandatory phase workflow from the then-current verified backend main.

Frontend NEXT independently in parallel:

`Complete active F03 — My Tournaments /dashboard/tournaments`, while retaining the explicit cross-repo status `FRONTEND MOCK / BACKEND PENDING` until registrations/tournaments backend implementation exists.

## 9. End-of-session update template

Every working chat must update the relevant sections above and maintain a concise terminal checkpoint.

### Latest session checkpoint

- Date: `2026-09-09`
- Repo changed: `turnoment-backend` documentation only
- Workstream: `F03 cross-repo My Tournaments contract alignment`
- Status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT ONLY`
- Backend START_SHA: `b92213436c5acbc8cb40ce22d2d6e7dbe2b82f86`
- Backend branch: `docs/f03-my-tournaments-contract`
- Backend Issue: `#9`
- Frontend accepted baseline: `4afb49e913d5fd7e2420031ae957fde2e79e3e8a`
- Frontend active F03 branch: `phase/f03-my-tournaments`
- Frontend draft PR: `#39`
- Cross-repo state: `FRONTEND MOCK / BACKEND PENDING`
- Backend implementation/migrations: `NONE`
- Backend NEXT remains: `P02 — Games / Catalog Foundation`
- Exact NEXT for this documentation checkpoint: `review diff, run backend CI, merge only if green; do not claim a backend phase completion`
