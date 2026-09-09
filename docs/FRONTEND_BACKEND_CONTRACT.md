# Frontend ↔ Backend Contract Baseline

Frontend source: `sajadkhavas/turnoment`

Latest terminal frontend baseline before active F05:

`864fe1491739b06c763be487a73a589c7e0f3609` — F04 terminal closeout / `/dashboard/matches` `FINAL_PRIVATE`

Active frontend workstream:

- F05 — Result Submission `/matches/$id/result`
- frontend START_SHA: `864fe1491739b06c763be487a73a589c7e0f3609`
- frontend branch: `phase/f05-result-submission`
- frontend Issue: `sajadkhavas/turnoment#44`

This document prevents a frontend screen from being considered product-complete while its mutable data/business behavior has no backend owner.

## Existing / active frontend surfaces

| Frontend surface | Backend owner | Contract |
|---|---|---|
| `/` homepage | discovery/content | planned `GET /api/v1/discovery/home/` |
| `/tournaments` | tournaments | planned `GET /api/v1/tournaments/` |
| `/tournaments/{id}` | tournaments/registrations | planned detail + registration commands |
| `/games` | games | planned `GET /api/v1/games/` |
| `/centers` | gaming_centers | planned `GET /api/v1/gaming-centers/` |
| `/centers/{id}` | gaming_centers | planned `GET /api/v1/gaming-centers/{id}/` |
| `/ranking` | rankings | planned `GET /api/v1/rankings/` |
| `/rules` | rulesets/game policies | planned `GET /api/v1/rulesets/` |
| `/host` | gaming_centers/onboarding | planned application command |
| `/login` | accounts | P01 OTP/session contract below |
| `/register` | accounts | P01 OTP/session contract below |
| `/dashboard` | player dashboard | private identity via P01; player dashboard projection exists on the frontend contract side and backend domain expansion remains phased |
| `/dashboard/profile` | accounts/player profile | `PATCH /api/v1/auth/me/profile/` |
| `/dashboard/tournaments` | registrations/tournaments | planned `GET /api/v1/me/tournaments/` |
| `/dashboard/matches` | matches/results/disputes | planned `GET /api/v1/me/matches/` |
| `/matches/{id}/result` | results | planned `GET/POST /api/v1/matches/{id}/result/` under F05 contract below |

## P01 — Authentication / identity contract

The current Lovable `/login` and `/register` forms still display password-oriented legacy UI. They are UI scaffolding only and MUST converge onto one phone-OTP flow; the frontend must not invent password account behavior for players.

### Same-origin web flow

1. `GET /api/v1/auth/csrf/` — establishes/returns CSRF token.
2. `POST /api/v1/auth/otp/request/` — canonical Iran mobile input; returns opaque `challenge_id`, expiry and resend timing.
3. `POST /api/v1/auth/otp/verify/` — verifies six-digit OTP, creates player account/profile when first seen, and establishes Django session.
4. `GET /api/v1/auth/me/` — private current-account projection.
5. `PATCH /api/v1/auth/me/profile/` — mutable player profile fields.
6. `POST /api/v1/auth/logout/` — terminates authenticated session.
7. `GET /api/v1/players/{gamer_tag}/` — anonymous-safe public player projection.

OTP request/verify are CSRF-protected. Frontend must send the CSRF token on unsafe same-origin requests and include session credentials after verification.

### P01 ownership

Backend-authoritative:
- canonical phone identity;
- account active state;
- OTP expiry, request cooldown/window and attempts;
- session authentication state;
- gamer-tag uniqueness;
- platform roles/permissions;
- private/public identity boundary.

Frontend-owned:
- OTP input presentation;
- transitions/animations/countdown rendering;
- visual onboarding layout.

Public player responses never contain `phone`, `email`, `interview_opt_in`, group names or permission data.

## Planned frontend surfaces already approved

| Frontend surface | Backend owner | Planned contract |
|---|---|---|
| `/games/{slug}` | games | `GET /api/v1/games/{slug}/` |
| `/players/{username}` | players | now backed by P01 public player identity; competitive stats expand later |
| `/dashboard/tournaments` | registrations/tournaments | `GET /api/v1/me/tournaments/` |
| `/dashboard/matches` | matches/results/disputes | `GET /api/v1/me/matches/` |
| `/matches/{id}` | matches | `GET /api/v1/matches/{id}/` + state commands |
| `/matches/{id}/result` | results | F05 planned `GET/POST /api/v1/matches/{id}/result/`; confirmation remains a separate later command/workstream |
| `/matches/{id}/dispute` | disputes | dispute create/read/evidence endpoints |
| `/challenges` | challenges | list/create/respond endpoints |
| `/challenges/{id}` | challenges | detail/state endpoints |
| `/rivalries/{id}` | rivalries | `GET /api/v1/rivalries/{id}/` |
| `/live` | matches/tournaments | live projection contract |
| `/stories` | stories | published content contracts |
| venue dashboard surfaces | gaming_centers/tournament ops | authenticated venue operator contracts |

## F03 — My Tournaments cross-repo contract

Cross-repo status: `FRONTEND MOCK / BACKEND PENDING`

Backend owner: `registrations/tournaments`

Planned authenticated endpoint:

`GET /api/v1/me/tournaments/`

F03 does not start or reorder a backend domain phase. The owning tournaments/registrations implementation must be delivered in its accepted backend phase order with its own Issue, branch, migrations/tests, CI, PR and closeout evidence. Backend NEXT remains `P02 — Games / Catalog Foundation`.

### Authentication / authorization

- Django Session Authentication is the web authentication truth.
- Browser requests include cookies with `credentials: include`.
- The endpoint is private and MUST enforce authentication/authorization server-side; the frontend dashboard route guard is only a UX/navigation boundary.
- No bearer token stored in `localStorage` is part of this contract.

### Query contract

Optional query parameters:

- `state=upcoming|live|completed`; absence means all lifecycle groups visible to the current player.
- `game=<stable-game-id>`; relational filtering uses stable game identity, not display name.
- `page=<positive-integer>`; absence means page 1.

### Response projection

```text
summary
  total
  upcoming
  live
  completed

games[]
  gameId
  name

items[]
  tournamentId
  tournamentSlug
  title
  game { gameId, name }
  venue { gamingCenterId, name, city }
  startsAt
  timezone
  formatLabel
  lifecycleState
  registrationState
  checkInState
  participation
  result
  nextAction

pagination
  currentPage
  totalPages
  totalItems
```

Authoritative enums:

- lifecycle: `upcoming | live | completed | cancelled`
- registration: `pending | confirmed | waitlisted | rejected | cancelled`
- check-in: `not-required | not-open | open | completed | missed`
- participation: individual or team projection with stable team ID and role
- next action: `view | check-in | view-bracket | view-results`

Backend owns tournament-list membership, lifecycle, registration/check-in/participation/result truth, summary, pagination and next action. Frontend may localize labels, format offset-aware dates in the supplied IANA timezone and own presentation/search navigation. It MUST NOT infer those authoritative states.

## F04 — My Matches cross-repo contract

Cross-repo status: `FRONTEND MOCK / BACKEND PENDING`

Backend owners:

- match identity/lifecycle/scheduling/check-in/list membership: `matches`
- score/result confirmation/finalization/rating delta projection: `results`
- dispute status/decision projection: `disputes`

Planned authenticated endpoint:

`GET /api/v1/me/matches/`

This endpoint is a private current-player projection. F04 documents the projection only; it does **not** implement the matches/results/disputes backend domains and does not change backend phase order. Backend NEXT remains `P02 — Games / Catalog Foundation`.

### Authentication / authorization

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Backend MUST scope the list to the authenticated player's permitted match participation and enforce this server-side.
- Frontend dashboard guards are UX/navigation boundaries only.
- No localStorage bearer-token contract is introduced.

### Query contract

Optional query parameters:

- `state=upcoming|action-required|completed|disputed`; absence means `all`.
- `kind=tournament|challenge`; absence means `all`.
- `game=<stable-game-id>`; uses stable identity, never display name as relation key.
- `page=<positive-integer>`; absence means page 1.

Frontend validates navigation state, but backend API validation remains authoritative.

### Response projection

```text
player
  playerId
  gamerTag

summary
  total
  upcoming
  actionRequired
  completed
  disputed

games[]
  gameId
  name

items[]
  matchId
  game
    gameId
    name
  competition
    kind: tournament | challenge
    competitionId
    title
    tournamentSlug?      # tournament only
    roundLabel            # tournament string; challenge null
  opponent
    participantId
    kind: player | team
    displayTag
  venue?                  # nullable
    gamingCenterId
    name
    city
  startsAt
  timezone
  formatLabel
  lifecycleState
  checkInState
  resultState
  disputeState
  attention
  result?                 # finalized result only

pagination
  currentPage
  totalPages
  totalItems
```

`startsAt` and a finalized result's `finalizedAt` are offset-aware ISO datetimes. `timezone` is an IANA timezone for local civil-time rendering.

### Authoritative enums / integrity

`lifecycleState`:

- `scheduled`
- `ready`
- `live`
- `awaiting-result`
- `awaiting-confirmation`
- `disputed`
- `completed`
- `cancelled`

`checkInState`:

- `not-required`
- `not-open`
- `open`
- `completed`
- `missed`

`resultState`:

- `not-open`
- `reportable`
- `awaiting-confirmation`
- `disputed`
- `finalized`
- `void`

`disputeState`:

- `none`
- `open`
- `under-review`
- `resolved`

`attention`:

- `none`
- `check-in`
- `submit-result`
- `confirm-result`
- `dispute`

A finalized `result` contains:

- `playerScore`: non-negative integer
- `opponentScore`: non-negative integer
- `outcome`: `win | loss | draw | void`
- `ratingDelta`: integer or null, backend-authoritative
- `finalizedAt`: offset-aware ISO datetime

Required integrity decisions:

- `completed` requires `resultState=finalized` and a finalized result projection;
- non-finalized result states do not expose a finalized result;
- `cancelled` uses `resultState=void`;
- `disputed` lifecycle requires `resultState=disputed` and an active dispute state;
- `check-in` attention requires check-in open;
- `submit-result` attention requires result reportable;
- `confirm-result` attention requires `awaiting-confirmation`;
- `dispute` attention requires an active dispute;
- summary and pagination truth are backend-owned.

### Ownership and workstream boundary

Backend owns:

- current player's match-list membership and scope;
- lifecycle/ready/live/cancelled truth;
- schedule/venue/competition/opponent identity;
- check-in applicability/state;
- whether a result is reportable/awaiting confirmation/finalized/void;
- final score, outcome and rating delta;
- dispute state and whether a dispute is active/resolved;
- attention projection and summary/pagination counts.

Frontend may:

- localize enum labels and copy;
- format dates in the supplied timezone;
- choose visual hierarchy/responsive presentation;
- keep state/kind/game/page filters in validated URL search.

Frontend MUST NOT infer winner, final score, rating delta, submission eligibility, confirmation eligibility, dispute eligibility/outcome or match lifecycle from timestamps/local values.

F04 My Matches is the list/attention surface only. Result Submission and Dispute are separate frontend workstreams mapped to their existing dedicated backend owners/contracts. F04 does not imply those mutation flows are already implemented.

### Integration gate

Until matches/results/disputes backend domains and the authenticated projection are implemented, permission-tested and merged under the accepted backend phase protocol, F04 remains:

`FRONTEND MOCK / BACKEND PENDING`

A frontend merge may freeze the final frontend architecture and Django adapter mapping, but must never be described as live backend integration before that backend evidence exists.

## F05 — Result Submission cross-repo contract

Cross-repo status: `FRONTEND MOCK / BACKEND PENDING`

Backend owner: `results`

F05 is a private current-player mutation surface for one Match. This section refines the previously reserved `/matches/{id}/result` contract; it does **not** implement the results domain and does not change backend phase order. Backend NEXT remains `P02 — Games / Catalog Foundation`.

### Planned endpoints

Read projection:

`GET /api/v1/matches/{matchId}/result/`

Submit command:

`POST /api/v1/matches/{matchId}/result/`

Result confirmation is intentionally not part of F05 and will use its own later command/workstream.

### Authentication / authorization / CSRF

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Backend MUST authorize that the authenticated player is the permitted participant for this Match and may view/submit its result state.
- Route-level frontend Session checks are UX/navigation only and never replace backend object authorization.
- The unsafe POST is CSRF-protected and consumes the existing P01 CSRF contract (`GET /api/v1/auth/csrf/` + `X-CSRFToken`).
- No localStorage bearer token is introduced.

### Read projection

```text
matchId
revision                     # opaque concurrency token
submissionState              # reportable | awaiting-confirmation | finalized | disputed | unavailable
player
  participantId
  displayTag
opponent
  participantId
  kind                       # player | team
  displayTag
game
  gameId
  name
competition
  kind                       # tournament | challenge
  competitionId
  title
  tournamentSlug?            # tournament only
  roundLabel                 # tournament string; challenge null
venue?                       # nullable
  gamingCenterId
  name
  city
startsAt                     # offset-aware ISO datetime
timezone                     # IANA timezone
formatLabel
scorePolicy
  minScore                   # non-negative integer
  maxScore                   # non-negative integer or null
  allowDraw
reportedScore?               # nullable; required when awaiting-confirmation
  playerScore
  opponentScore
  reportedAt
finalResult?                 # nullable; only when finalized
  playerScore
  opponentScore
  outcome                    # win | loss | draw | void
  ratingDelta                # integer or null
  finalizedAt
```

Required projection integrity:

- `reportable` exposes neither `reportedScore` nor `finalResult`;
- `awaiting-confirmation` requires `reportedScore` and does not expose `finalResult`;
- `finalized` requires authoritative `finalResult`;
- states other than `finalized` do not expose final outcome/rating truth;
- `disputed` and `unavailable` are never submit-eligible;
- `maxScore`, when present, is not lower than `minScore`.

### Submit command

POST JSON body:

```text
revision
playerScore
opponentScore
```

- scores are non-negative integers and must satisfy the backend-owned `scorePolicy`;
- equal scores are rejected when `allowDraw=false`;
- frontend validation is convenience only; backend repeats all validation and eligibility checks;
- frontend MUST NOT derive winner/outcome/rating delta from submitted scores.

The request carries an `Idempotency-Key` header generated once for a logical submit attempt. Backend implementation must define persistent/transaction-safe idempotency semantics before this endpoint becomes live. Repeating the same key for the same authenticated participant/Match/command must not create a second logical result submission. Key reuse with conflicting command content must fail closed under the owning results phase.

### Concurrency / stale state

`revision` is opaque and backend-generated. Submission eligibility is checked atomically against current Match/result truth. If the read projection is stale or eligibility changed, backend returns a typed `stale` outcome with the current revision/state path rather than accepting based on frontend state.

The frontend reloads authoritative data after a stale outcome. It never assumes that timestamps/local state make a result reportable.

### Typed action outcomes

The backend response contract is one of:

`accepted`
- `receiptId`
- `matchId`
- `status = awaiting-confirmation | finalized`
- authoritative `reportedScore`
- `finalResult` only if status is finalized

`validation_error`
- field/form errors for authoritative score/rule validation

`stale`
- current opaque `revision`

`unavailable`
- reason: `not-reportable | disputed | finalized | cancelled`

`already_submitted`
- authoritative existing status `awaiting-confirmation | finalized`
- authoritative `reportedScore`
- `finalResult` only when finalized

HTTP status mapping may be refined in the owning results implementation, but typed response semantics above are the frontend contract. Authentication/permission failures still use normal private API 401/403 behavior, and missing Match/result scope uses 404 according to the final implementation policy.

### Workstream boundary

F05 owns only reporting the score. It does not own:

- opponent result confirmation;
- dispute creation/evidence;
- moderation decision;
- winner/final-result/rating computation.

Those remain separate backend transitions/workstreams. The frontend may show server-returned final truth but must not manufacture it.

### Integration gate

Until the owning results/matches backend slice implements the endpoints, authorization, CSRF, idempotency, atomic stale checks, validation and tests under the mandatory backend phase protocol, F05 remains:

`FRONTEND MOCK / BACKEND PENDING`

Frontend finality may freeze the route/repository/UI contract ahead of backend implementation, but that is not evidence the API is live.

## Contract rules

1. Display names are not relational keys. APIs use stable identifiers; public entities may additionally use slugs/gamer tags.
2. Frontend never calculates authoritative rating, financial totals, settlement, tournament lifecycle or final match result.
3. `Tournament Rating` and `Challenge Rating` are separate backend concepts.
4. Challenge eligibility is backend-authoritative; the approved rule is 30 finalized valid matches, regardless of wins/losses.
5. Public SEO pages receive server-fetchable backend data so TanStack Start can SSR meaningful HTML.
6. Backend-controlled SEO fields may include slug, SEO title, description, index policy, canonical policy, OG media and publication state.
7. Mock data is temporary UI scaffolding, not durable backend schema or evidence that the API exists.
8. When Lovable or a frontend workstream adds a new mutable field or action, its backend owner and contract must be added here before the associated product integration is considered complete.
9. Private endpoints enforce authentication and object/user scope server-side even when the frontend also has a route guard.
