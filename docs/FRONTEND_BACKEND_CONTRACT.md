# Frontend ↔ Backend Contract Baseline

Frontend source: `sajadkhavas/turnoment`

Latest terminal frontend baseline before active F04:

`df7c4e8c6c60c35616bba1143814b5d2a7a408c7` — F03 terminal closeout / `/dashboard/tournaments` `FINAL_PRIVATE`

Active frontend workstream:

- F04 — My Matches `/dashboard/matches`
- frontend START_SHA: `df7c4e8c6c60c35616bba1143814b5d2a7a408c7`
- frontend branch: `phase/f04-my-matches`
- frontend Issue: `sajadkhavas/turnoment#41`

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
| `/matches/{id}/result` | results | result submit/confirm endpoints |
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
