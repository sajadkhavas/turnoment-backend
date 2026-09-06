# Backend Phase Registry

> Every phase owner/chat MUST follow the root `PHASE_COMPLETION_PROTOCOL.md`. A phase is not DONE until both this registry and its phase-specific GitHub Issue contain final evidence.

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

Status: `IN PROGRESS`

- START_SHA: `2d3ba917dc7c1f041faa3ff6d3e5bf2babddbd19`
- Branch: `phase/p01-accounts-player-auth`
- Tracking Issue: `#4`
- Frontend baseline: `8d5736d788235e3e99765a5332f79f0cba861482`
- Scope: custom account identity, Iran mobile normalization, player profile/gamer tag, OTP lifecycle, sender abstraction, Django session + CSRF, private/public identity APIs
- Implementation END_SHA: pending
- PR: pending
- CI: pending
- Merge SHA: pending
- Registry freeze: pending

### P01 acceptance gates

- [x] Root mandatory phase-completion protocol prepared
- [x] Official-source audit recorded
- [x] Custom user model designed as initial accounts migration
- [x] Canonical Iran mobile identity
- [x] PlayerProfile / gamer-tag identity boundary
- [x] Persistent OTP challenge + request-state lifecycle
- [x] OTP sender abstraction with production-disabled default
- [x] Session + CSRF API contract
- [x] Private `me` and profile mutation contract
- [x] Public player privacy projection
- [x] Abuse/privacy/CSRF test coverage prepared
- [ ] Migration drift check green
- [ ] Full CI green on Python 3.12 and 3.14
- [ ] PR reviewed / no open blocker
- [ ] Implementation merged to main
- [ ] Phase Issue and registry frozen with exact final evidence

## Next domain phases

After P01 closes, implementation proceeds through games/catalog, gaming centers/resources, tournaments/registrations, rankings, then match/result/challenge/rivalry slices in lockstep with frontend completion.
