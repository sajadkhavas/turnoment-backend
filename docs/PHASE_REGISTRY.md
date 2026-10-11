# Backend Phase Registry

> Every phase owner/chat MUST follow the root `PHASE_COMPLETION_PROTOCOL.md`. A phase is not DONE until both this registry and its phase-specific GitHub Issue contain final evidence.

## B00 — Final Backend Execution Lock

Status: `DONE / MERGED / FROZEN`

- Tracking Issue: `#45`
- START_SHA: `46b3f47b38068675ed8a0941a871438e51abd6a2`
- Branch: `phase/b00-final-backend-execution-lock-20261010`
- Frozen frontend contract SHA: `1668109bae5ec7abb5e022e5857ffa65cc131501`
- Purpose: lock ten bounded implementation workstreams and mother/integration acceptance against the final frontend.
- Financial execution: `DEFERRED / DO NOT IMPLEMENT`
- Planning commit: `d53e0afa409392c883804077aeb9f7aa99afab4a`
- PR: `#46`
- Push gate `38066380699`: PASS on Python 3.12 / 3.14
- PR-context gate `38066400575`: PASS on Python 3.12 / 3.14
- B00 merge SHA: `c3186ab98cf00e7d7575d301134f9cd29d1dd54f`
- Post-main gate `38066482086`: PASS on Python 3.12 / 3.14
- Child Issues: `#47-#56`
- Child branches: `phase/b01-*` through `phase/b10-*`
- Execution lock: `docs/B00_FINAL_BACKEND_EXECUTION_LOCK.md`
- Ten chat prompts: `docs/B00_TEN_CHAT_PROMPTS.md`

B00 does not alter the frozen completion evidence for P00/P01. Runtime domain implementation remains pending until its owning workstreams merge and pass final integration acceptance.

---

## B01 — Core Contract & Integration Foundation

Status: `IMPLEMENTATION MERGED / CLOSEOUT IN PROGRESS` (this registry snapshot precedes the terminal closeout merge and CI).

- Tracking Issue: `#47`
- START_SHA: `0f5d44646b608106ad20db97ec8c559fa084e6ce`
- Frozen frontend contract SHA: `1668109bae5ec7abb5e022e5857ffa65cc131501`
- Implementation branch: `phase/b01-core-contract-integration`
- Agent implementation END_SHA: `cbb6e5b7dbad3ab3130882c0079c9f40654724e6`
- Final reviewed implementation HEAD: `91dd280dc5b7355e0c7f557de0bee29e56547061`
- Source-audit correction: `docs/OFFICIAL_SOURCES.md` amended in final reviewed head; official Django 6.1 links aligned.
- Implementation PR: `#59` — MERGED with exact expected-head lock
- Exact-head push CI: `38144471947` — PASS Python 3.12 / 3.14
- Exact-head PR-context CI: `38144474605` — PASS Python 3.12 / 3.14
- Open unresolved PR review threads at merge: `0`
- Implementation merge/main SHA: `f0e1cc898d7d6170c9d54062a27dd681a962bd23`
- Post-implementation main CI: `38144591828` — PASS Python 3.12 / 3.14
- Closeout branch: `closeout/b01-core-contract-freeze`
- Closeout PR: pending at the time of this initial registry snapshot; the live Issue #47 records terminal closeout SHA and CI after merge.
- Scope: stable identifiers, opt-in DRF error/pagination helpers, persistent audit/event outbox primitives, PostgreSQL uniqueness checks, idempotency/rollback tests; preserved P01 auth and CSRF. No new public endpoints.
- Financial execution added: `NO`.
- Integration dependencies: B99/B10 own outbox dispatch/retry/consumer registration; B09 owns exactly-once ranking consumer effects; B99 owns any system/meta frontend SHA migration.

B01 is not terminally `DONE` until closeout PR merges, post-closeout `main` CI passes, and Issue #47 records exact terminal evidence.


---

## P00 — Backend Foundation & Frontend Contract Baseline

Status: `DONE / MERGED / FROZEN`

- Bootstrap SHA: `16540a37809c0c4e06a1cd5f6ee03bd88002fdc4`
- START_SHA: `16540a37809c0c4e06a1cd5f6ee03bd88002fdc4`
- Implementation branch: `phase/p00-backend-foundation`
- Frontend baseline: `8d5736d788235e3e99765a5332f79f0cba861482`
- Target stack: Django 6.1 + DRF 3.18 + PostgreSQL + Redis + Celery
- Implementation END_SHA: `f96a8beaf0fe6810880343413868d64fa3e8c089`
- Final reviewed branch SHA: `be7fe0c9426dc67d729848d9cf7c4325d2dc7619`
- Implementation PR: `#2`
- Final pre-merge CI: run `34041103523` — PASS on Python 3.12 and 3.14
- Implementation merge SHA: `1347052022dcc55b6ce3097f707022e742b2fb82`
- Registry closeout PR: `#3`
- Frozen main SHA after closeout: `2d3ba917dc7c1f041faa3ff6d3e5bf2babddbd19`
- Final post-merge CI: run `34041256027` — PASS on Python 3.12 and 3.14

### P00 acceptance gates

- [x] Empty repository bootstrapped without secrets
- [x] Dedicated phase branch
- [x] Official-source audit recorded
- [x] Environment-split Django settings with fail-closed production config
- [x] DRF v1 baseline and default authenticated policy
- [x] PostgreSQL configuration baseline
- [x] Redis cache baseline
- [x] Celery integration baseline
- [x] Liveness/readiness/meta endpoints
- [x] Frontend contract baseline recorded
- [x] Engineering rules recorded
- [x] Local PostgreSQL/Redis compose baseline
- [x] Tests for system endpoints
- [x] GitHub Actions quality gate green on Python 3.12 and 3.14
- [x] PR diff reviewed; open review threads: 0
- [x] P00 implementation merged to main
- [x] Registry frozen with exact merge evidence

---

## P01 — Accounts, Player Identity & Authentication Foundation

Status: `DONE / MERGED / FROZEN`

- START_SHA: `2d3ba917dc7c1f041faa3ff6d3e5bf2babddbd19`
- Implementation branch: `phase/p01-accounts-player-auth`
- Tracking Issue: `#4`
- Frontend baseline: `8d5736d788235e3e99765a5332f79f0cba861482`
- Scope: custom account identity, Iran mobile normalization, player profile/gamer tag, OTP lifecycle, sender abstraction, Django session + CSRF, private/public identity APIs
- Implementation END_SHA: `fd53c04b2452a84da10f5cdb9ad92c237e166f21`
- Final reviewed implementation branch SHA: `1901c4dbb85dcc1a2e91c61aab754b2f8dbd4fc1`
- Implementation PR: `#5`
- Green implementation PR CI: run `34044591737` — PASS on Python 3.12 and 3.14
- Final pre-merge documentation CI: run `34044761851` — PASS on Python 3.12 and 3.14; 29 tests PASS; migration drift `No changes detected`; production deployment checks PASS
- Implementation merge SHA: `46734475831064e124357dbc57d603c47b2b9245`
- Open review threads before implementation merge: `0`
- Closeout branch: `closeout/p01-freeze` created from the exact implementation merge SHA
- Official-source closeout re-review: `2026-09-06` — no architecture deviation found
- Closeout PR: `#6`
- Closeout pre-freeze CI: run `34045720546` — PASS on Python 3.12 and 3.14
- Final closeout registry-head CI: run `34045794057` — PASS on Python 3.12 and 3.14
- Closeout review threads: `0`
- Closeout merge SHA / frozen main SHA: `8488e70dbc5f9926eecaa5c9756fc4a1d7156e08`
- Post-closeout main CI: run `34045855470` — PASS on Python 3.12 and 3.14
- Terminal registry-status branch: `closeout/p01-status-final`
- Terminal status-finalization merge SHA and its final `main` CI are recorded in Issue `#4` after merge, per `PHASE_COMPLETION_PROTOCOL.md`.

### P01 acceptance gates

- [x] Root mandatory phase-completion protocol committed
- [x] Official-source audit recorded and re-reviewed before closeout
- [x] Custom user model established in the first accounts migration
- [x] Canonical Iran mobile identity
- [x] PlayerProfile / gamer-tag identity boundary
- [x] Persistent OTP challenge + request-state lifecycle
- [x] Latest OTP invalidates earlier active login challenge
- [x] Failed OTP delivery does not burn request quota/cooldown
- [x] OTP sender abstraction with production-disabled default
- [x] Session + CSRF API contract
- [x] Private `me` and profile mutation contract
- [x] Public player privacy projection
- [x] Abuse/privacy/CSRF/replay tests
- [x] Migration drift check green
- [x] Full implementation CI green on Python 3.12 and 3.14
- [x] Implementation PR reviewed / no blocker / review threads: 0
- [x] Final implementation documentation-head CI green
- [x] Implementation merged to main
- [x] Closeout branch created from exact implementation merge SHA
- [x] Closeout PR #6 full CI green and review threads: 0
- [x] Closeout PR #6 merged
- [x] Post-closeout `main` CI green on Python 3.12 and 3.14
- [x] Registry status finalized as `DONE / MERGED / FROZEN`

## Next domain phases

After P01 closes, implementation proceeds through games/catalog, gaming centers/resources, tournaments/registrations, rankings, then match/result/challenge/rivalry slices in lockstep with frontend completion.
