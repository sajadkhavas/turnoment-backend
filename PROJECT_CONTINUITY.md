# TURNOMENT — PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**
>
> This file is the current operational checkpoint for the whole Turnoment project. Read it before making changes. Update it before ending the session — even when the work is incomplete, blocked, or only partially implemented.

Last checkpoint update: `2026-09-07`

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

Current `main` SHA at this checkpoint:

`4d714579fc97d1400b5a2b50b680d93b090ceac5`

Latest merged frontend work:

- PR `#1` — Tournament Discovery completion
- Merge SHA: `4d714579fc97d1400b5a2b50b680d93b090ceac5`
- Post-merge Frontend Quality Gate: run `34104818438` — PASS

Frontend next phase:

`F00 — Frontend Production Architecture Foundation`

Frontend branch already created:

`phase/f00-frontend-production-foundation`

Frontend F00 START_SHA:

`4d714579fc97d1400b5a2b50b680d93b090ceac5`

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

Current `main` SHA at this checkpoint:

`113e597ec94aaaae02186daf09c98fc1900cb62c`

## 3. Backend phase state

- `P00 — Backend Foundation & Frontend Contract Baseline` → `DONE / MERGED / FROZEN`
- `P01 — Accounts, Player Identity & Authentication Foundation` → `DONE / MERGED / FROZEN`
- Next backend phase: `P02 — Games / Catalog Foundation`

Historical backend phase evidence remains authoritative in:

- `PHASE_COMPLETION_PROTOCOL.md`
- `docs/PHASE_REGISTRY.md`
- phase-specific GitHub Issues / PRs

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

From this checkpoint onward, pages must be built as the FINAL frontend architecture, not temporary mock-only screens that require a later SSR/router/SEO reconstruction phase.

Target flow:

`Route → validated params/search → loader/service → typed repository contract → Mock adapter now → Django HTTP adapter later → UI`

Important current frontend truth:

- Homepage: strong visual reference, production contract migration still pending.
- Tournament Discovery: merged/build-green, but repository/service adapter migration still pending before global backend-ready status.
- Tournament Detail: prototype only; fake local registration and in-person payment copy must be replaced.
- Ranking: visual/frontend prototype; productionization pending.
- Player Profile: visual/frontend prototype; productionization pending.
- Legacy ecommerce routes still exist and are not tournament product architecture.

## 6. Backend NEXT

### P02 — Games / Catalog Foundation

Status: `PLANNED`

START_SHA when begun:

`113e597ec94aaaae02186daf09c98fc1900cb62c`

Expected direction:

- game identity / slug
- game publication/activation state
- platform support metadata
- tournament-facing game configuration boundary
- backend-authoritative public game catalog
- API contract aligned with frontend Game Listing / future Game Detail
- admin management
- permissions
- tests / migrations / CI / registry evidence

Do not invent publisher/legal rule content as hardcoded truth; game-specific policy/rules should remain versionable/configurable.

## 7. Cross-repo API alignment

Backend changes that alter API shape or business semantics must update the recorded frontend contract expectations.

Frontend changes that introduce new backend-authoritative data must be mapped to a backend owner/domain/API before the corresponding frontend page is considered final.

If a session changes this cross-repo contract, update `PROJECT_CONTINUITY.md` in BOTH repositories.

## 8. Exact NEXT

Backend NEXT:

`Start P02 — Games / Catalog Foundation from backend main SHA 113e597ec94aaaae02186daf09c98fc1900cb62c.`

Frontend NEXT, independently in parallel:

`Complete F00 — Frontend Production Architecture Foundation from frontend main SHA 4d714579fc97d1400b5a2b50b680d93b090ceac5.`

## 9. End-of-session update template

Every working chat must update the relevant sections above and maintain a concise terminal checkpoint.

### Latest session checkpoint

- Date: `2026-09-07`
- Repo changed: `none yet — continuity bootstrap only`
- Workstream: `Project continuity bootstrap`
- Status: `IN PROGRESS until continuity PR is merged`
- START_SHA backend: `113e597ec94aaaae02186daf09c98fc1900cb62c`
- START_SHA frontend: `4d714579fc97d1400b5a2b50b680d93b090ceac5`
- Blockers: `none`
- Exact NEXT: `merge continuity bootstrap, then begin P02 when backend work resumes`
