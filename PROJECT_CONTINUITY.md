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

Repository: `sajadkhavas/turnoment-backend`

Current accepted backend main / F15 docs-alignment START_SHA:

`1977db3c9995336166907b9fd85ac26093e6c254`

P00 and P01 are terminally frozen. Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Cross-repo frontend contracts may be documented ahead of runtime implementation, but they do not start/reorder backend phases and MUST remain represented as:

`FRONTEND MOCK / BACKEND PENDING`

until an owning backend domain is actually implemented, permission-tested and merged.

## 3. F14 Teams alignment — terminal documentation truth

- backend Issue `#25` — CLOSED / COMPLETED;
- docs branch `docs/f14-player-teams-contract`;
- accepted docs head `26a2182f6d67a63a4a1dc9eef3daf7a030c85b50`;
- PR `#26` — MERGED;
- PR Backend Quality Gate `34539140468` — PASS on Python 3.12 and 3.14;
- accepted backend main `1977db3c9995336166907b9fd85ac26093e6c254`;
- post-main Backend Quality Gate `34539329509` — PASS on Python 3.12 and 3.14;
- no Teams Python/model/migration/serializer/view/URL runtime implementation was added.

Frontend F14 `/dashboard/teams` is now terminally frozen independently under frontend Issue #71. That does not change backend runtime state or phase order.

## 4. Active cross-repo alignment — F15 Player Challenge Hub

Frontend repository: `sajadkhavas/turnoment`

Frontend route: `/dashboard/challenges`

Frontend START_SHA / current frozen main at F15 start:

`398e963f1ecdbe86013ce3b0052c4e1891f48854`

Backend tracking Issue: `#27`

Backend docs branch: `docs/f15-player-challenge-hub-contract`

Contract source: `docs/F15_PLAYER_CHALLENGE_HUB_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ONLY`

The preserved Lovable Challenge Hub already has a read/list scaffold, but create/respond/cancel behavior was not backed by a permanent mutation contract and must not be treated as final product truth.

Planned authenticated API family:
- `GET /api/v1/me/challenges/`
- `GET /api/v1/me/challenges/opponents/`
- `POST /api/v1/me/challenges/`
- `POST /api/v1/me/challenges/{challengeId}/response/`
- `POST /api/v1/me/challenges/{challengeId}/cancel/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, dependencies and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. Permanent Challenge product/security truth

- Tournament Rating and Challenge Rating are separate.
- Challenge unlock requires **30 finalized valid Matches**, not wins.
- no wager/betting/stake mechanics.
- Challenge access, eligibility, lifecycle, revisions, allowed commands, result and rating changes are backend-authoritative.
- frontend must not infer eligibility or lifecycle from timestamps, raw Match history, local counters or button state.
- current-player Challenge list membership/scope is backend-authoritative.
- opponent search returns server-authorized eligible candidates with stable `playerId`; UI never creates a relationship from display text alone.
- Challenge creation uses stable `opponentPlayerId`, stable `gameId` and stable `formatId` from backend-projected options/search results.
- unsafe create/respond/cancel commands use Django Session + accepted P01 CSRF bootstrap and `X-CSRFToken`.
- create/respond/cancel use one idempotency key per logical attempt.
- respond/cancel include an opaque Challenge revision and fail closed on stale state.
- accepted/stale/unavailable mutation outcomes cause the frontend to reload authoritative Challenge loader truth rather than optimistically owning lifecycle state.
- no localStorage/sessionStorage bearer contract exists.
- F15 does not invent Challenge Detail. Navigation from Hub is restricted to typed targets for already accepted routes.

## 6. Official source decisions retained for F15

Reviewed current official guidance:
- Django CSRF protection: `https://docs.djangoproject.com/en/6.0/ref/csrf/`;
- Django CSRF AJAX guidance: `https://docs.djangoproject.com/en/dev/howto/csrf/`;
- Django REST Framework SessionAuthentication: `https://www.django-rest-framework.org/api-guide/authentication/`;
- Django REST Framework AJAX/CSRF: `https://www.django-rest-framework.org/topics/ajax-csrf-cors/`.

Applied implications:
- safe GET endpoints are side-effect free;
- unsafe POST commands require CSRF when using SessionAuthentication;
- authentication identifies the caller, while object/capability authorization remains server-side;
- frontend guards are UX/navigation only and never replace object authorization;
- no CSRF exemption is introduced by this docs alignment.

Frontend also audits current TanStack Router mutation invalidation and W3C modal-dialog guidance independently.

## 7. Exact F15 backend alignment NEXT

1. keep this alignment diff documentation-only;
2. require exact compare from `1977db3c9995336166907b9fd85ac26093e6c254`;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #27;
5. require mergeable=true, unresolved review threads=0 and exact pre-merge backend `main` lock;
6. merge with expected-head lock;
7. require post-main Backend Quality Gate PASS;
8. reverify exact live backend `main`;
9. record terminal docs-alignment evidence in Issue #27 and close completed;
10. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`.

Frontend F15 independently completes its implementation/QA/closeout chain. Completion of backend Issue #27 is contract alignment only and MUST NOT be described as live Challenge backend implementation.
