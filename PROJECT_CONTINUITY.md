# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-12`

## 1. Continuation law

Every backend chat/agent MUST:
1. read this file and `PHASE_COMPLETION_PROTOCOL.md`;
2. verify exact current `main` before mutation;
3. read `docs/PHASE_REGISTRY.md` before starting/reordering a backend phase;
4. use a dedicated branch/Issue/PR;
5. never claim DONE from chat memory;
6. keep cross-repo frontend contracts explicit without pretending planned APIs are live;
7. preserve exact SHA/CI/PR/Issue evidence;
8. obey `docs/ENGINEERING_RULES.md`, including explicit public-endpoint permission/authentication policy under the authenticated global default;
9. keep docs-only alignment work out of Python/models/migrations/serializers/views/URLs/settings/dependencies/workflows/phase-registry;
10. keep runtime phase order authoritative even when frontend architecture is frozen first.

## 2. Current backend truth

Repository: `sajadkhavas/turnoment-backend`

Current live backend `main` / F23 documentation-alignment START_SHA:

`215fae68d8003b8df6c034b228d1121d96b0be18`

P00 and P01 remain terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry remains authoritative. Cross-repo documentation alignment MUST NOT reorder runtime work.

Current runtime truth remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

## 3. Accepted documentation alignments

F19 Public Gaming Center Discovery is terminal: Issue #35 CLOSED / COMPLETED; PR #36 MERGED; backend main `b6421e1e76e846c89d799fe4860bc11c8242f2f8`; PR-context Backend Quality Gate `34641469931` and post-main `34641761119` PASS on Python 3.12 / 3.14.

F20 Public Gaming Center Detail is terminal: Issue #37 CLOSED / COMPLETED; PR #38 MERGED; backend main `e8e48061cba201b3a12ac534ef97f22565bea5a3`; PR-context gate `34653701760` and post-main `34653883656` PASS on Python 3.12 / 3.14.

F21 Public Player Ranking is terminal documentation alignment: Issue #39 CLOSED / COMPLETED; PR #40 MERGED; backend main `44f18e462f63c625bc02e07ef93c15f1c385dcd0`; PR-context Backend Quality Gate `34658090539` and post-main `34658179049` PASS on Python 3.12 / 3.14.

F22 Public Player Profile is terminal documentation alignment: Issue #41 CLOSED / COMPLETED; PR #42 MERGED; exact docs head `be805235925af8b70a6e8d183e5f8f363dd7c9cb`; backend merge/main `215fae68d8003b8df6c034b228d1121d96b0be18`; exact-head `34688994229`, PR-context `34689064802`, and post-main `34689119713` all PASS on Python 3.12 / 3.14.

None of these alignments added owning runtime-domain implementation or reordered backend phases.

## 4. Active cross-repo alignment — F23 Host Application

Frontend repository: `sajadkhavas/turnoment`.

Frontend route:

`/host`

Frontend F23 START_SHA:

`e1aa1667f3c70a9e00d9664b1e20d3019587cab0`

Frontend exact accepted source checkpoint used for this alignment:

`e70de8ee4acc20014da6a0d10a4343ea26f3e1de`

Frontend tracking Issue:

`sajadkhavas/turnoment#104`

Backend tracking Issue:

`#43`

Backend docs branch:

`phase/f23-host-application-contract-docs`

Contract source:

`docs/F23_HOST_APPLICATION_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Frontend-reserved target endpoint:

`POST /api/v1/host-applications/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. F23 frontend contract checkpoint

The accepted F23 frontend source has exact-head evidence before backend documentation mutation:
- focused F23 run `34702167115` — PASS;
- focused artifact `10300084668` — digest `sha256:d1de24c54a127f66cc097d05e0ef17e9cc631ec61aa3e687421bc782bb8c87d3`;
- Full Frontend Quality Gate `34702167120` — PASS;
- Full browser-QA artifact `10300094875` — digest `sha256:363f125ae1c2e476383ad660ab7fca3ef3094f23a0a6916c55e1837eed02c649`.

Frontend request fields are `venueName`, `managerName`, `phone`, `city`, `area`, `stationCount`, `games`, and nullable `description`. Persian/Arabic digits and Iranian mobile input are normalized before the typed request boundary. Production has no fixture fallback.

Frontend success requires a runtime-validated v1 receipt containing `schemaVersion=1`, server-issued `applicationId`, `state=received`, and offset-aware `submittedAt`.

## 6. Public write authentication / CSRF boundary

Current backend global DRF defaults use `SessionAuthentication` and `IsAuthenticated`.

F23 is intentionally a public acquisition form. A future runtime implementation must explicitly declare both:
- `permission_classes = [AllowAny]`;
- an authentication policy that does not accidentally inherit session-authenticated CSRF behavior for this anonymous public create endpoint.

The accepted documentation target is a session-independent public submission endpoint, for example an empty per-view authentication class list together with explicit `AllowAny`. This keeps a logged-in browser from being treated differently from an anonymous browser solely because a session cookie is present.

This documentation decision does not implement the endpoint and does not weaken authentication defaults elsewhere.

## 7. F23 validation / abuse / privacy ownership

Future backend authority includes:
- request validation and normalization at the API boundary;
- authoritative application identity, receipt state and submission timestamp;
- persistence and duplicate/idempotency policy;
- rate-limit/abuse controls;
- access controls for stored application PII;
- retention/deletion policy when the owning runtime phase is implemented.

DRF throttling may be used as one policy layer, but must not be described as complete brute-force or denial-of-service protection.

No public list/detail/read endpoint is implied by F23. The public API only reserves creation of an application receipt.

Frontend validation remains defense in depth and must not replace backend validation.

## 8. Official DRF decisions reviewed for F23

Current official Django REST framework guidance reviewed before this documentation mutation:
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/ — `AllowAny` explicitly communicates unrestricted public access; permissions are separate from authentication.
- Authentication: https://www.django-rest-framework.org/api-guide/authentication/ — authentication policy is independently configurable per view.
- Settings: https://www.django-rest-framework.org/api-guide/settings/ — authentication and permission defaults are separate API policies.
- AJAX / CSRF / CORS: https://www.django-rest-framework.org/topics/ajax-csrf-cors/ — JavaScript clients using session authentication must account for CSRF behavior.
- Serializers: https://www.django-rest-framework.org/api-guide/serializers/ — request deserialization/validation belongs at the serializer boundary.
- Throttling: https://www.django-rest-framework.org/api-guide/throttling/ — throttles control request rate/policy and are not a complete security or DoS defense.

Applied decision: the future F23 public create route must be explicit about both permission and authentication policy; server-side validation and abuse controls remain authoritative; no runtime code is authorized in this alignment.

## 9. F23 documentation-alignment acceptance chain

Required chain:
1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F23_HOST_APPLICATION_CONTRACT.md` from backend START `215fae68d8003b8df6c034b228d1121d96b0be18`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #43;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend-main lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend main;
10. record terminal documentation-alignment evidence in Issue #43 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`;
12. keep runtime truth `FRONTEND MOCK / BACKEND PENDING` until an owning runtime phase actually ships the endpoint.
