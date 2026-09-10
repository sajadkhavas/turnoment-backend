# F11 — Player Settings & Notification Preferences Cross-Repo Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ONLY`

Frontend route: `/dashboard/settings`

Frontend workstream: `F11 — Player Settings & Notification Preferences`

Frontend tracking Issue: `sajadkhavas/turnoment#62`

Backend tracking Issue: `#19`

Backend START_SHA: `e1d8d86f9b44a2874afc29f4ef9de13aeb34d9f7`

Runtime status: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains: `P02 — Games / Catalog Foundation`

## 1. Purpose and bounded ownership

F11 defines only the future private current-player notification-preference surface required by `/dashboard/settings`. It does **not** implement preference persistence, notification generation, delivery, web push, service workers, serializers, views, URL registration, models, migrations, tasks, or backend phase work.

The scope is intentionally aligned with the notification kinds already accepted by F10:

- optional player-controlled categories: `tournament`, `match`, `challenge`;
- essential categories: `account`, `system` — always enabled and not user-disableable.

Preferences affect only whether future optional notification events are delivered to the player's notification surface once the owning backend implementation exists. They do not alter competitive/business truth.

Backend remains authoritative for:
- authenticated player ownership;
- persisted preference values and defaults;
- opaque revision/concurrency truth;
- authorization of reads and writes;
- validation of preference payloads;
- application of preferences to future optional notification delivery;
- mandatory delivery policy for `account` and `system` notices.

Frontend may:
- present the three optional switches;
- explain that account/system notices remain required;
- keep an unsaved local form draft;
- submit the current opaque revision with the desired optional values;
- render backend-returned saved or stale state.

Frontend MUST NOT:
- delete or hide existing F10 inbox items as a consequence of changing preferences;
- infer tournament/match/challenge membership, eligibility, lifecycle, result, rating, dispute, or moderation truth;
- disable essential account/security/system notices;
- invent arbitrary privacy controls or challenge business rules;
- claim or simulate a live web-push/PWA subscription flow.

## 2. Authentication / authorization / CSRF

All F11 endpoints are private current-player surfaces.

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Backend resolves the settings owner only from the authenticated session; no player ID is accepted from the browser for ownership.
- The unsafe PATCH is CSRF-protected and consumes the existing P01 bootstrap contract (`GET /api/v1/auth/csrf/` + `X-CSRFToken`).
- No localStorage/sessionStorage bearer-token authentication is introduced.

## 3. Planned endpoints

### Read preferences

`GET /api/v1/me/settings/notification-preferences/`

Successful projection:

```text
revision                         # opaque non-empty concurrency token
optional
  tournament                     # boolean
  match                          # boolean
  challenge                      # boolean
required
  account                        # literal true
  system                         # literal true
```

The backend chooses and persists defaults. The frontend must never guess whether an optional category is enabled in production.

### Save preferences

`PATCH /api/v1/me/settings/notification-preferences/`

Request JSON:

```text
revision                         # exact opaque revision from latest read/saved projection
optional
  tournament                     # boolean
  match                          # boolean
  challenge                      # boolean
```

Unknown preference fields are rejected. `account` and `system` are deliberately absent from the writable request schema.

Successful response:

```text
outcome: saved
settings
  revision
  optional { tournament, match, challenge }
  required { account: true, system: true }
```

Stale/concurrent response:

```text
outcome: stale
message                          # final user-safe explanation or stable error projection
settings                         # authoritative current projection including current revision
```

The owning implementation may return HTTP 409 for the stale outcome. Frontend must replace its authoritative baseline with the returned current projection rather than overwriting newer state silently.

## 4. Revision / concurrency law

`revision` is opaque and backend-generated. It exists only for compare-and-set semantics and must not encode business meaning on the frontend.

The save command atomically verifies the supplied revision against the current persisted preference revision. If it is stale, the backend rejects the write and returns current authoritative settings. A successful save produces the current authoritative projection and a revision suitable for the next edit.

F11 does not use optimistic authority: the frontend may show local form intent while a request is pending, but it treats only a returned `saved` projection as persisted truth.

## 5. Preference semantics

Optional category preferences apply prospectively:
- changing a preference does not mutate, delete, mark read, or reorder existing F10 inbox items;
- disabling `tournament` does not unregister a player from tournaments;
- disabling `match` does not alter Match scheduling/result/dispute truth;
- disabling `challenge` does not decline, block, accept, or otherwise mutate any Challenge domain state;
- re-enabling a category does not synthesize historical notifications that were not delivered while disabled unless a future owning domain explicitly defines such behavior.

Mandatory categories:
- `account=true` is invariant;
- `system=true` is invariant;
- the client receives these values for transparent rendering but cannot submit them as writable fields.

## 6. Typed failure classes

The owning backend implementation must distinguish at least:
- unauthenticated/session expired;
- CSRF/security rejection;
- stale revision/concurrent edit;
- invalid preference payload;
- unexpected service failure.

The frontend must not display raw server exceptions or stack information.

## 7. UI states supported by this contract

The final F11 frontend can represent:
- loading/pending;
- authenticated normal state;
- load error/retry;
- session-expired redirect;
- pristine and locally modified form states;
- save pending;
- save success/status feedback;
- save failure with retry-safe retained draft;
- stale/concurrent result with authoritative refresh;
- mandatory account/system notice explanation.

## 8. PWA / push boundary

F11 notification preferences are **not** a browser push-subscription implementation.

No service worker registration, Push API permission request, push subscription key, endpoint, device token, notification permission state, or push-delivery guarantee is defined here. Those require a dedicated accepted PWA/push contract/workstream.

This preserves the F10 statement that push/delivery settings are separate from inbox read-state behavior without fabricating an unavailable production capability.

## 9. Runtime / phase-order gate

This file is cross-repo alignment only.

Until an owning settings/notifications backend phase implements persistence and these endpoints with authorization, CSRF, concurrency tests, migrations where needed, CI, PR, merge and closeout evidence:

`FRONTEND MOCK / BACKEND PENDING`

F11 documentation alignment does not start or reorder P02. Backend NEXT remains `P02 — Games / Catalog Foundation`.
