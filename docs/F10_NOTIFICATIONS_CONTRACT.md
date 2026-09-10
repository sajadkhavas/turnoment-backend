# F10 — Player Notifications Inbox Cross-Repo Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ONLY`

Frontend route: `/dashboard/notifications`

Frontend workstream: `F10 — Player Notifications Inbox`

Frontend tracking Issue: `sajadkhavas/turnoment#59`

Backend tracking Issue: `#17`

Backend START_SHA: `38dccbf213d5f439e56cd608e3e4ac419d5092d1`

Runtime status: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains: `P02 — Games / Catalog Foundation`

## 1. Purpose and ownership

F10 defines the future private notification-inbox projection needed by the player dashboard. This document does **not** implement notification persistence, event fan-out, delivery, serializers, views, URL routes, models, migrations, Celery tasks or push delivery.

Future backend owner: player notifications/inbox domain fed by authoritative platform events.

Backend remains authoritative for:
- recipient membership and visibility;
- notification existence and stable identity;
- notification kind/content projection;
- occurrence time;
- read state and read timestamp;
- total/unread summary;
- filtering, ordering and pagination;
- typed navigation target projection;
- authorization of every private request.

Frontend may:
- validate URL filter/search state for navigation;
- localize labels around the supplied projection;
- format supplied timestamps;
- group items visually by date;
- render read/unread emphasis;
- navigate only through accepted typed targets.

Frontend MUST NOT infer tournament/match/challenge lifecycle, winner, rating, eligibility, moderation, dispute or result truth from notification copy or timestamps.

## 2. Authentication / authorization / CSRF

All F10 endpoints are private current-player surfaces.

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Backend scopes every list/read command to the authenticated player.
- A notification identifier belonging to another player must never disclose private content or ownership.
- Unsafe read-state commands are CSRF-protected and consume the existing P01 CSRF bootstrap contract (`GET /api/v1/auth/csrf/` + `X-CSRFToken`).
- No localStorage/sessionStorage bearer-token contract is introduced.

## 3. Planned endpoints

### List inbox

`GET /api/v1/me/notifications/`

Optional query parameters:
- `state=unread|read`; absence means all;
- `kind=tournament|match|challenge|account|system`; absence means all;
- `page=<positive-integer>`; absence means page 1.

The backend returns newest-first ordering. Frontend does not re-sort authoritative inbox order.

### Mark one notification read

`POST /api/v1/me/notifications/{notificationId}/read/`

No business payload is required. The server resolves current-player ownership from Session + notification identity.

This command is idempotent by domain semantics: repeating it for an already-read notification returns the authoritative current read state without creating duplicate side effects.

### Mark all notifications read

`POST /api/v1/me/notifications/read-all/`

This command marks all currently unread notifications in the authenticated player's inbox as read, regardless of the visual filter currently selected in the frontend.

This command is idempotent by domain semantics. Repeating it when unread count is already zero is a successful no-op and must not create duplicate side effects.

## 4. List projection

```text
summary
  total                    # non-negative integer
  unread                   # non-negative integer, <= total

items[]
  notificationId           # stable opaque identifier
  kind                     # tournament | match | challenge | account | system
  title                    # non-empty final user-facing projection
  body                     # non-empty final user-facing projection
  occurredAt               # offset-aware ISO datetime
  readAt                   # offset-aware ISO datetime or null
  target                   # typed navigation target or null

pagination
  currentPage              # positive integer
  totalPages               # non-negative integer
  totalItems               # non-negative integer
```

Integrity requirements:
- `summary.unread <= summary.total`;
- `pagination.totalItems` represents the current filtered result set, not the global summary;
- empty result sets may use `totalPages=0` with `currentPage=1`;
- `readAt=null` means unread; non-null `readAt` means read;
- timestamps are offset-aware;
- notification title/body are projections of backend-owned event truth, not instructions to let the frontend infer missing competitive state;
- list membership and order are backend-owned.

## 5. Typed navigation targets

F10 must not accept arbitrary URLs from the notification payload. The backend emits a nullable discriminated target that the frontend maps to known application routes.

Accepted F10 target kinds are intentionally limited to already-existing/accepted routes:

```text
null

{ kind: "my-tournaments" }
{ kind: "my-matches" }
{ kind: "tournament-detail", tournamentSlug: <stable slug> }
{ kind: "result-submission", matchId: <stable match id> }
{ kind: "match-dispute", matchId: <stable match id> }
{ kind: "player-profile" }
```

Target integrity:
- `tournament-detail` requires a valid stable tournament slug;
- result/dispute targets require a valid stable Match identifier;
- a target never conveys authorization; destination APIs must independently authorize access;
- target identifiers are routing identifiers only and cannot be treated as competitive truth;
- F10 does **not** invent a Challenge Detail URL while that route contract is not yet accepted;
- future target kinds require an explicit contract revision rather than arbitrary `href` passthrough.

A Challenge notification may therefore have `target=null` until an accepted Challenge Detail route exists.

## 6. Mark-one response

Successful response projection:

```text
notificationId
readAt                   # authoritative offset-aware ISO datetime
unreadCount              # authoritative current-player unread count
```

Integrity:
- the returned notification is read;
- `unreadCount` is non-negative;
- retrying the command returns authoritative current state without incrementing/decrementing twice.

Expected failure classes for the owning implementation phase:
- unauthenticated session;
- notification unavailable/not visible to current player;
- CSRF/security failure;
- unexpected service failure.

Frontend must not display raw server errors.

## 7. Mark-all response

Successful response projection:

```text
markedCount              # number transitioned from unread to read by this command
readAt                   # server timestamp applied/representative for the command
unreadCount              # authoritative unread count after the command
```

Integrity:
- `markedCount` is non-negative;
- successful completion returns the authoritative current unread count;
- repeated successful call with no new unread notifications may return `markedCount=0`;
- mutation is scoped only to the authenticated player's inbox.

## 8. Frontend URL/navigation state

The frontend may keep shareable inbox filters in URL search:
- `state=unread|read`; absence = all;
- `kind=tournament|match|challenge|account|system`; absence = all;
- `page` omitted for page 1.

The backend repeats validation and remains authoritative. Invalid frontend URL search values fail closed to accepted defaults before repository calls.

## 9. UI-state requirements supported by this contract

The final F10 page can represent:
- normal inbox;
- unread/read styling from `readAt`;
- backend-owned total/unread summary;
- all/unread/read filtering;
- domain-kind filtering;
- pagination;
- empty filtered state;
- loading/pending;
- load error/retry;
- mark-one pending/success/error;
- mark-all pending/success/error;
- unauthenticated/session-expired return to Login;
- nullable CTA target.

No push-notification preference/settings UI is implied by F10. Delivery-channel preferences belong to a separate Settings/PWA contract.

## 10. Runtime / phase-order gate

This document is cross-repo alignment only.

Until the owning notification domain has its own accepted backend Issue/branch, persistence/event semantics, permissions, tests, migrations where needed, CI, PR, merge and closeout evidence:

`FRONTEND MOCK / BACKEND PENDING`

This documentation alignment does not start or reorder P02. Backend NEXT remains `P02 — Games / Catalog Foundation`.
