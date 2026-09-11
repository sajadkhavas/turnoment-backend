# F15 — Player Challenge Hub Cross-Repo Contract

Status: `DOCUMENTATION ALIGNMENT — RUNTIME PENDING`

Frontend route: `/dashboard/challenges`

Backend tracking Issue: `#27`

Backend START_SHA: `1977db3c9995336166907b9fd85ac26093e6c254`

Frontend F15 START_SHA: `398e963f1ecdbe86013ce3b0052c4e1891f48854`

Runtime truth: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains: `P02 — Games / Catalog Foundation`

## 1. Purpose and boundary

F15 productionizes the private Player Challenge Hub architecture without implementing or reordering the backend Challenge domain.

The frontend may finalize its typed repository, runtime validation, deterministic QA adapter, Django adapter mapping and UI states ahead of backend runtime delivery. Mutable/business-significant Challenge truth remains backend-authoritative.

Permanent boundary:

`authenticated current-player Challenge scope → validated status/page query → authoritative Hub projection → typed commands → authoritative reload → UI`

F15 does not define a Challenge Detail route. It also does not introduce wagers, stakes, betting, prize escrow or any financial Challenge mechanic.

## 2. Permanent competitive truth

- Tournament Rating and Challenge Rating are distinct systems.
- Challenge unlock requires `30` finalized valid Matches, not wins.
- frontend never computes unlock from local Match rows.
- frontend never computes Challenge Rating or rating delta.
- frontend never decides whether an opponent/game/format is eligible.
- frontend never derives Challenge lifecycle, command capability, final result or winner.

## 3. Authentication / authorization / CSRF

All endpoints below are private and use the accepted Django Session web-authentication contract.

- browser requests use `credentials: include`;
- backend scopes data to the authenticated player and performs object/capability authorization server-side;
- frontend route guards are UX/navigation boundaries only;
- no bearer token in localStorage/sessionStorage exists;
- unsafe POST commands use the accepted P01 CSRF bootstrap `GET /api/v1/auth/csrf/` and send `X-CSRFToken`;
- safe GET endpoints must remain side-effect free.

Current official references:
- Django CSRF: `https://docs.djangoproject.com/en/6.0/ref/csrf/`;
- Django AJAX CSRF: `https://docs.djangoproject.com/en/dev/howto/csrf/`;
- DRF authentication / SessionAuthentication: `https://www.django-rest-framework.org/api-guide/authentication/`;
- DRF AJAX/CSRF: `https://www.django-rest-framework.org/topics/ajax-csrf-cors/`.

## 4. Hub read contract

Planned endpoint:

`GET /api/v1/me/challenges/`

Optional query:
- `status=all|incoming|outgoing|active|action-required|completed`; absence = `all`;
- `page=<positive-integer>`; absence = `1`.

Response projection:

```text
player
  playerId
  username
  gamerTag

access
  unlocked
  canCreate
  challengeRating
  finalizedValidMatches
  requiredFinalizedMatches       # exactly 30 under current product law

creation
  games[]
    gameId
    name
    formats[]
      formatId
      label
  opponentSearchMinChars
  noteMaxLength

summary
  incoming
  outgoing
  active
  completed

items[]
  challengeId
  revision                       # opaque concurrency token
  direction                      # incoming | outgoing
  lifecycle
  statusLabel
  actionRequiredLabel?
  opponent
    playerId
    username
    gamerTag
    avatarInitials
    challengeRating?
  game
    gameId
    name
  format
    formatId
    label
  createdAtLabel
  responseDeadlineLabel?
  note?
  match?
    matchId?
    startsAtLabel?
    venueLabel?
    contextLabel?
  result?
    outcome                      # win | loss | draw | void
    scoreLabel?
    ratingDelta?
    completedAtLabel
  allowedCommands[]              # accept | decline | cancel
  navigationTarget?              # typed target only; no arbitrary href

pagination
  currentPage
  totalPages
  totalItems
```

Authoritative lifecycle enum:
- `invitation-pending`
- `invitation-expired`
- `invitation-declined`
- `accepted`
- `match-ready`
- `awaiting-result`
- `action-required`
- `completed`
- `cancelled`

Typed Hub navigation targets are limited to already-accepted frontend surfaces:
- `my-matches`
- `result-submission(matchId)`
- `match-dispute(matchId)`

F15 does not allow an arbitrary URL and does not invent Challenge Detail.

### Read integrity

Backend owns and frontend runtime validation enforces at minimum:
- `requiredFinalizedMatches` equals current Challenge unlock policy (`30`);
- `canCreate` cannot be true while `unlocked=false`;
- summary values are non-negative and filtered pagination count cannot exceed the account-level summary total represented by the lifecycle groups;
- current page cannot exceed total pages for non-empty results;
- page challenge IDs are unique;
- every challenge has a non-empty opaque revision;
- `accept`/`decline` may only be exposed on incoming pending invitations;
- `cancel` may only be exposed on outgoing pending invitations;
- completed Challenge requires authoritative final result;
- non-completed Challenge never exposes a final result;
- navigation targets that require `matchId` use a stable server-projected Match ID;
- no `allowedCommands` or navigation target is synthesized from timestamps or labels by frontend.

## 5. Opponent search contract

Planned endpoint:

`GET /api/v1/me/challenges/opponents/?q=<query>&game=<stable-game-id>`

Purpose: resolve user-entered search text into backend-authorized, Challenge-eligible stable player identities before creation. The create command never uses gamer tag/display text as a relationship key.

Response:

```text
query
items[]
  playerId
  username
  gamerTag
  avatarInitials
  challengeRating?
```

Rules:
- backend validates minimum query length according to the Hub `creation.opponentSearchMinChars` projection;
- results exclude the current player;
- results are already scoped to players the caller may challenge for the selected game under current server policy;
- no private phone/email/permission data is exposed;
- stable `playerId` from a result is used in create command.

## 6. Create Challenge command

Planned endpoint:

`POST /api/v1/me/challenges/`

Headers:
- session cookie via `credentials: include`;
- `X-CSRFToken`;
- `Idempotency-Key: <opaque client key>`.

Request:

```text
opponentPlayerId
  stable player identity from authoritative opponent search
gameId
  stable game identity from creation options
formatId
  stable format identity nested under selected game
note
  optional trimmed note within server-projected max length
```

Backend revalidates unlock/canCreate, opponent eligibility, self-challenge prevention, game/format relationship, duplicate/conflicting active Challenge policy, note policy and authorization inside the command transaction.

Typed outcomes:
- `accepted { challengeId, revision }`
- `validation_error { fields }`
- `unavailable { message }`
- `conflict { message }`
- `session_expired { message }`

The same idempotency key is reused only when retrying the same logical create attempt. A new logical create attempt gets a new key.

Frontend does not optimistically add a Challenge to its list. After `accepted`, it invalidates/reloads authoritative Hub data.

## 7. Respond command

Planned endpoint:

`POST /api/v1/me/challenges/{challengeId}/response/`

Headers: session + CSRF + `Idempotency-Key`.

Request:

```text
revision
  opaque revision from current Hub item
action
  accept | decline
```

Server authorization requires an incoming pending invitation currently actionable by the authenticated player.

Typed outcomes:
- `accepted { challengeId, revision }`
- `stale { message }`
- `unavailable { message }`
- `session_expired { message }`

`stale` means the supplied revision/capability is no longer current. Frontend must fail closed and reload authoritative Hub truth; it does not force or reconstruct the transition.

## 8. Cancel outgoing invitation command

Planned endpoint:

`POST /api/v1/me/challenges/{challengeId}/cancel/`

Headers: session + CSRF + `Idempotency-Key`.

Request:

```text
revision
  opaque revision from current Hub item
```

Server authorization requires an outgoing pending invitation currently cancellable by the authenticated player.

Typed outcomes:
- `accepted { challengeId, revision }`
- `stale { message }`
- `unavailable { message }`
- `session_expired { message }`

Frontend reloads authoritative Hub truth after accepted/stale/unavailable outcomes.

## 9. Frontend UX contract implications

F15 UI must provide:
- authenticated populated list;
- locked access state;
- create-enabled and create-disabled states;
- creation modal with game, format, opponent search/result selection and optional note;
- opponent-search pending/empty/error states;
- per-card accept/decline/cancel pending state;
- explicit confirmation for decline/cancel where appropriate;
- mutation success/error/stale/session-expired feedback;
- filtered empty/all empty states;
- loader pending/load error/retry;
- pagination;
- private `noindex,nofollow`;
- accessible keyboard/focus semantics for dialog/confirmations;
- responsive behavior at `375 / 390 / 430 / 768 / 1024 / 1440`.

Final user-facing copy must not mention mock data, API/backend waiting, placeholder state or implementation staging.

## 10. Runtime implementation boundary

This document does not implement:
- Challenge models/tables;
- migrations;
- serializers/views/URLs;
- permission classes;
- transactions/row locks/idempotency persistence;
- search indexes;
- Match scheduling/result/rating runtime logic.

When the owning backend Challenge phase is reached, it must implement these contracts under `PHASE_COMPLETION_PROTOCOL.md` with its own migrations, permission/CSRF/idempotency/stale/race tests, CI, PR and closeout.

Until then the cross-repo runtime truth remains exactly:

`FRONTEND MOCK / BACKEND PENDING`.
