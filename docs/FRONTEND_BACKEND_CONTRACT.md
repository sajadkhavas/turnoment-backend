# Frontend ↔ Backend Contract Baseline

Frontend source: `sajadkhavas/turnoment`

Accepted frontend baseline through F02:

`4afb49e913d5fd7e2420031ae957fde2e79e3e8a` — F02 terminal closeout / `/games/$slug` `FINAL_CURRENT`

Active frontend workstream:

- F03 — My Tournaments `/dashboard/tournaments`
- frontend branch: `phase/f03-my-tournaments`
- frontend Issue: `sajadkhavas/turnoment#38`
- frontend draft PR: `sajadkhavas/turnoment#39`

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

Planned authenticated endpoint, already approved in the baseline above:

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

Unknown/invalid query values must be rejected or normalized by the backend contract according to the owning phase's API validation decision; the frontend also validates navigation input but that never replaces backend validation.

### Response projection

The response supplies backend-authoritative page data:

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
  game
    gameId
    name
  venue
    gamingCenterId
    name
    city
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

`startsAt` is an offset-aware ISO datetime. `timezone` is the IANA timezone used when the product must render the tournament's local civil time.

### Authoritative enums

`lifecycleState`:

- `upcoming`
- `live`
- `completed`
- `cancelled`

`registrationState`:

- `pending`
- `confirmed`
- `waitlisted`
- `rejected`
- `cancelled`

`checkInState`:

- `not-required`
- `not-open`
- `open`
- `completed`
- `missed`

`participation` is a discriminated projection:

- `{ kind: "individual" }`
- `{ kind: "team", teamId, teamName, role: "captain" | "member" }`

`result` is nullable. When present it contains:

- `placement: positive integer | null`
- `matchesPlayed: non-negative integer`
- `wins: non-negative integer`

`nextAction`:

- `view`
- `check-in`
- `view-bracket`
- `view-results`

### Ownership rules for F03

Backend owns and returns:

- membership of the current player's tournament list;
- tournament lifecycle;
- registration state;
- check-in state and whether check-in is applicable/open/completed/missed;
- individual/team participation truth and team identity;
- result/placement/win projection;
- summary counts;
- pagination truth;
- the permitted/highest-priority `nextAction` projection.

Frontend may:

- localize enum labels into natural Persian;
- format the offset-aware datetime in the supplied timezone;
- choose responsive layout, icons, spacing and visual emphasis;
- keep filter/page navigation in validated URL search state.

Frontend MUST NOT infer authoritative lifecycle, registration, check-in, result, placement or allowed action from timestamps or local fixture values.

### Integration gate

Until the owning backend domain and this endpoint are implemented, permission-tested and merged under the mandatory backend phase protocol, F03's cross-repo status remains:

`FRONTEND MOCK / BACKEND PENDING`

A frontend-only merge may establish the final frontend architecture and permanent HTTP adapter mapping, but it must not be described as live backend integration or complete product integration before this backend gate exists.

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
