# F23 — Host Application Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/host`

Frontend tracking Issue: `sajadkhavas/turnoment#104`

Backend tracking Issue: `#43`

Backend START_SHA:

`215fae68d8003b8df6c034b228d1121d96b0be18`

Frontend F23 START_SHA:

`e1aa1667f3c70a9e00d9664b1e20d3019587cab0`

Frontend exact accepted source checkpoint used for this alignment:

`e70de8ee4acc20014da6a0d10a4343ea26f3e1de`

## 1. Scope and phase-order law

This file aligns the future backend host-application contract with frontend F23. It does **not** implement host-application runtime code, persistence, models, migrations, serializers, views, URLs, throttles, settings or deployment configuration and does not reorder backend phases.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Runtime remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

The F23 frontend may be frozen against this planned contract before backend integration, but the application submission must not be described as live until an accepted owning runtime phase implements, secures, tests and merges it.

## 2. Target endpoint

Frontend F23 reserves:

`POST /api/v1/host-applications/`

The endpoint is a public create-only acquisition boundary. No public list, detail, update, delete or search endpoint is implied.

Canonical successful creation response should use HTTP `201 Created` with the accepted receipt projection below. The existing frontend adapter accepts any successful 2xx response but runtime implementation should keep one canonical success status.

Unsupported methods should retain normal API method-not-allowed behavior.

## 3. External request contract

The JSON request field names are part of the accepted frontend/backend boundary and use the exact frontend names below:

```text
venueName: string
managerName: string
phone: string
city: string
area: string
stationCount: integer
games: string
description: string | null
```

Accepted bounds after frontend normalization:
- `venueName`: trimmed, 2..120 characters;
- `managerName`: trimmed, 2..120 characters;
- `phone`: canonical Iranian mobile form `+989xxxxxxxxx`;
- `city`: trimmed, 2..80 characters;
- `area`: trimmed, 2..120 characters;
- `stationCount`: integer 1..1000;
- `games`: trimmed, 2..300 characters;
- `description`: null or trimmed 1..1200 characters.

The future backend may use different internal/model field names, but the public v1 representation must either accept this exact external contract or coordinate a versioned frontend adapter change before activation.

Unknown request fields should not silently become stored business data.

## 4. Normalization and validation boundary

The accepted frontend currently performs defense-in-depth normalization before submission:
- Persian digits `۰..۹` and Arabic-Indic digits `٠..٩` are normalized to ASCII digits where required;
- `09xxxxxxxxx` and `989xxxxxxxxx` mobile forms are normalized to canonical `+989xxxxxxxxx` when valid;
- `stationCount` is converted to an integer;
- optional blank description is projected as `null`.

This does not make frontend validation authoritative.

Future backend implementation must independently validate the request, including:
- exact field allow-list;
- string bounds and required/nullable semantics;
- canonical phone policy and normalization/validation;
- integer range for station count;
- persistence-safe content bounds;
- any later domain constraints required by the owning host/venue model.

Canonical invalid-request status should be HTTP `400 Bad Request`. The accepted frontend also maps `422` to its validation state for compatibility, but that tolerance does not require the backend to use 422.

## 5. Successful receipt contract

A successful v1 response contains exactly the public-safe receipt needed by the acquisition UI:

```text
schemaVersion: 1
applicationId: string
state: received
submittedAt: offset-aware ISO datetime
```

Rules:
- `schemaVersion` is exactly `1`;
- `applicationId` is server-issued and stable for the stored application receipt; frontend currently accepts an opaque `[A-Za-z0-9_-]` token of length 1..128;
- `state` is exactly `received` for this v1 receipt;
- `submittedAt` is generated/owned by the backend and includes an explicit UTC offset;
- the backend must not echo private/internal review data, staff notes, abuse signals, secret identifiers or unrelated account state in this public receipt.

The frontend runtime-validates this response. A malformed 2xx body is treated as `invalid_response`, not success.

## 6. Frontend error projection

The accepted F23 frontend maps transport outcomes as follows:
- `400` or `422` → `validation`;
- `429` → `rate_limited`;
- network failure → `unavailable`;
- any other non-2xx status → `unavailable`;
- malformed successful JSON/contract → `invalid_response`.

Production does not fall back to fixture/demo success.

The future backend may return structured validation details for observability or later field-level integration, but F23 v1 does not currently depend on a specific error-body schema. Status-code semantics therefore remain the minimum cross-repo contract.

## 7. Public permission, authentication and CSRF policy

Current Turnoment backend global defaults are:
- `SessionAuthentication`;
- `IsAuthenticated`.

The host application is intentionally a public acquisition write. Future implementation must explicitly override the global permission policy with:

`AllowAny`

Permission alone is not sufficient to define this endpoint correctly because DRF authentication is a separate policy. If the route inherited `SessionAuthentication`, an otherwise public unsafe request from a browser that already has a valid session could enter session-authenticated CSRF enforcement while an anonymous request would not.

Therefore the accepted F23 target is **session-independent public submission**. The owning runtime implementation must explicitly select an authentication configuration that does not accidentally authenticate this create request through the session merely because a session cookie exists. An empty per-view authentication class list is one acceptable implementation consistent with this contract.

Consequences:
- anonymous and logged-in browsers get the same public application-submission semantics;
- receipt creation is not implicitly attached to `request.user` merely because cookies are present;
- disabling session authentication on this one future public endpoint does not alter authentication defaults elsewhere;
- if a future product requirement intentionally links applications to signed-in users, that is a new contract requiring explicit CSRF/authentication/frontend changes and tests.

This endpoint still requires HTTPS and normal deployment-origin/CORS hardening when browser and API origins differ.

## 8. Abuse, throttling and availability

A public write endpoint requires explicit abuse controls in its owning runtime phase.

The implementation must evaluate and test an appropriate combination of:
- anonymous request throttling/rate policy;
- server-side request validation and bounded payload sizes;
- duplicate/replay handling;
- operational logging/monitoring without leaking PII;
- infrastructure-level abuse/DoS controls where applicable.

DRF throttling is suitable as one request-rate policy layer and naturally maps exhausted requests to HTTP `429`, but official DRF guidance explicitly does not position built-in throttling as complete brute-force or denial-of-service protection.

Rate-limit values are **not** frozen by this documentation alignment. They belong to the owning runtime phase and deployment requirements.

## 9. Duplicate and idempotency boundary

The current F23 frontend does not send an idempotency key and does not define an automatic retry protocol.

The backend must not invent user-visible approval or deduplication meaning from display fields alone. Before runtime activation, the owning phase must deliberately choose and test duplicate/replay semantics, for example whether identical requests inside a bounded window create one application or separate receipts.

If a formal idempotency key becomes required, the external request/header contract must be coordinated with the frontend before activation.

## 10. PII and storage boundary

The request necessarily carries acquisition PII, especially `managerName` and `phone`.

Future backend implementation must:
- store only fields required for the accepted host-review workflow;
- restrict application access to explicitly authorized operational/admin surfaces;
- avoid exposing application records through anonymous read/list endpoints;
- avoid placing raw PII in public logs, metrics, error messages or receipt payloads;
- define retention/deletion behavior when the owning business workflow is implemented;
- treat any future verification documents or richer venue evidence as a separate accepted contract rather than silently extending F23 v1.

The F23 public receipt is deliberately minimal and does not expose review notes, internal status history or operator identity.

## 11. Server-owned business truth

Frontend F23 owns presentation, final public copy, form UX, client-side validation, accessibility/responsive behavior, SEO/canonical/robots, and deterministic dev/test fixtures behind the same repository interface.

Backend eventually owns:
- whether an application is accepted for persistence;
- authoritative application identity;
- authoritative receipt state/timestamp;
- validation and abuse decisions;
- duplicate/idempotency behavior;
- future review/approval lifecycle;
- any future relationship to a venue, organizer account or gaming-center record.

The frontend must not fabricate approval, host eligibility, licensing, review completion or venue activation.

`state=received` only confirms that the accepted runtime endpoint stored/accepted the submission according to its v1 create contract. It does not mean approved, verified, licensed or activated.

## 12. Official DRF documentation decisions

Reviewed before this docs-only alignment:

- Permissions — https://www.django-rest-framework.org/api-guide/permissions/
  - permissions are evaluated separately from authentication;
  - `AllowAny` explicitly communicates unrestricted public access and overrides the authenticated global permission default per view.
- Authentication — https://www.django-rest-framework.org/api-guide/authentication/
  - authentication policy is independently configurable per view;
  - authenticated requests that are later denied return 403 regardless of authentication scheme.
- Settings — https://www.django-rest-framework.org/api-guide/settings/
  - `DEFAULT_AUTHENTICATION_CLASSES` and `DEFAULT_PERMISSION_CLASSES` are distinct global policies and may be overridden deliberately.
- AJAX / CSRF / CORS — https://www.django-rest-framework.org/topics/ajax-csrf-cors/
  - JavaScript clients using session authentication must account for CSRF protection;
  - same-context session-authenticated AJAX is a distinct pattern from this session-independent public form.
- Serializers — https://www.django-rest-framework.org/api-guide/serializers/
  - deserialization and validation of incoming data belongs at the serializer/API boundary.
- Throttling — https://www.django-rest-framework.org/api-guide/throttling/
  - throttles control request rate/policy and may distinguish anonymous/authenticated clients;
  - built-in throttling is not a complete security or DoS defense and can have concurrency fuzziness.

Applied F23 decisions:
- future route is create-only and explicitly public;
- both permission and authentication policy are explicit;
- session cookies do not silently change public submission semantics;
- backend validation remains authoritative;
- `429` is reserved for accepted rate-limit policy;
- no runtime implementation or phase reordering occurs in this alignment.

## 13. Current runtime truth

At this documentation checkpoint, `POST /api/v1/host-applications/` does **not** exist in backend runtime.

The accepted frontend production repository remains fail-closed when the endpoint/configuration is unavailable. Deterministic fixture behavior is for non-production development/test/visual QA only.

No documentation statement may claim live host-application integration until an owning runtime phase implements and merges the accepted behavior.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Runtime remains:

`FRONTEND MOCK / BACKEND PENDING`

## 14. Documentation-alignment acceptance

This alignment may change exactly two Markdown files:
1. `PROJECT_CONTINUITY.md`;
2. `docs/F23_HOST_APPLICATION_CONTRACT.md`.

It must not change Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows or `docs/PHASE_REGISTRY.md`.

Required evidence before closing backend Issue #43:
- one docs commit / two Markdown files / ahead 1 / behind 0;
- Backend Quality Gate PASS on Python 3.12 and 3.14;
- docs PR-context gate PASS;
- mergeable=true;
- unresolved review threads=0;
- exact pre-merge backend-main lock;
- expected-head merge;
- post-main Backend Quality Gate PASS;
- exact live backend-main verification;
- terminal evidence in Issue #43 and close `completed`;
- Backend NEXT still exactly `P02 — Games / Catalog Foundation`.
