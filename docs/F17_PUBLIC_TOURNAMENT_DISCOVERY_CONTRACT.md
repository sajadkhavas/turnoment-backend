# F17 — Public Tournament Discovery Contract

Status: `PLANNED CONTRACT / FRONTEND MOCK / BACKEND PENDING`

Frontend route: `/tournaments`

Backend owner: tournaments/registrations, with game identity sourced from Games/Catalog and venue identity/verification sourced from Gaming Centers once those owning phases exist.

Planned endpoint:

`GET /api/v1/tournaments/`

This document defines the stable frontend-facing discovery projection only. It does not authorize runtime implementation or reorder backend phases. Backend NEXT remains exactly `P02 — Games / Catalog Foundation`.

## 1. Purpose

The public tournament inventory is the authoritative discovery/list surface for users comparing competitions before opening one tournament detail. It needs one SSR-friendly anonymous read contract that accepts validated filter/sort/page input and returns an already-filtered, already-sorted, paginated projection.

The browser must not download an arbitrary tournament collection and then become authoritative for filtering, ordering, featured selection, verification, lifecycle or capacity truth.

## 2. Query contract

All query parameters are optional.

```text
game=<stable-game-id-or-approved-slug>
city=<stable-city-value>
date=today|tomorrow|weekend|week
status=open|filling|closed|upcoming
format=1v1|team|single-elim|double-elim|round-robin
price=free|lt300|300-500|gt500
verified=true
sort=suggested|soonest|limited|cheapest|prize
page=<positive-integer>
```

Rules:
- absence means the backend-defined default for the field;
- unsupported values fail safely under the future API implementation and are never interpreted as display-name relationships;
- `game` and `city` values must map to stable accepted domain identifiers/values;
- `verified=false` is equivalent to the filter being absent; `verified=true` means only venue projections whose authoritative verification state is true;
- page numbering is 1-based;
- frontend URL validation is navigation safety only; backend validation remains authoritative.

## 3. Response envelope

```text
schemaVersion

filters
  games[]
    gameId
    slug
    name
  cities[]
    value
    label

activeQuery
  game?
  city?
  date?
  status?
  format?
  price?
  verified
  sort
  page

featuredTournamentId?         # nullable/absent when no curated item is exposed

items[]
  tournamentId
  tournamentSlug
  title
  game
    gameId
    slug
    name
  venue
    gamingCenterId
    name
    verified
    city
    district
  lifecycleState
  registrationState
  startsAt
  timezone
  displayDate
  displayTime
  formatLabel
  bracketFormatLabel
  capacity
    limit
    registered
    remaining
  entryFee
    amount
    currency                   # IRR
  fixedPrize
    amount
    currency                   # IRR

pagination
  currentPage
  totalPages
  totalItems
  pageSize
```

The response is intentionally a list projection, not a copy of the full tournament-detail model. Detail-only rules, participant previews, bracket preview and registration commands remain owned by the existing tournament detail/registration contracts.

## 4. Authoritative enums

`lifecycleState`:
- `registration_open`
- `filling`
- `registration_closed`
- `upcoming`
- `check_in`
- `in_progress`
- `completed`
- `cancelled`

`registrationState`:
- `open`
- `filling`
- `closed`
- `upcoming`
- `unavailable`

`date` navigation buckets:
- `today`
- `tomorrow`
- `weekend`
- `week`

`format` filter values:
- `1v1`
- `team`
- `single-elim`
- `double-elim`
- `round-robin`

`price` filter values:
- `free`
- `lt300`
- `300-500`
- `gt500`

`sort` values:
- `suggested`
- `soonest`
- `limited`
- `cheapest`
- `prize`

Labels shown to Persian users remain frontend presentation copy; these stable values are protocol keys.

## 5. Integrity rules

- every item has stable tournament ID + slug;
- game and venue relations use stable IDs; display names are never relation keys;
- `capacity.limit` is positive when capacity is finite;
- `capacity.registered >= 0`;
- `capacity.registered <= capacity.limit`;
- `capacity.remaining = max(0, capacity.limit - capacity.registered)`;
- frontend does not recompute or override capacity truth even when it can derive the same arithmetic;
- `venue.verified` is authoritative and cannot be inferred from presence in the result set;
- `entryFee` and `fixedPrize` are non-negative explicit money objects;
- `startsAt` is offset-aware and `timezone` is an IANA timezone;
- lifecycle and registration states must be compatible; a cancelled/completed tournament is never exposed as registration-open/filling;
- `featuredTournamentId`, when supplied, must identify one item in the current projection or be omitted/null;
- result order is authoritative for the accepted `sort` mode;
- pagination totals are backend-owned;
- empty `items` is a valid response and must not trigger fabricated production content.

## 6. Filtering / sorting ownership

Future backend implementation owns all filtering and ordering semantics.

Examples:
- `soonest` sorts by authoritative schedule, not Persian display-date text;
- `limited` uses authoritative remaining-capacity semantics;
- `cheapest` uses authoritative `entryFee.amount`;
- `prize` uses authoritative `fixedPrize.amount`;
- `suggested` may use an accepted deterministic backend policy but must not become an undisclosed browser heuristic;
- `date=today|tomorrow|weekend|week` is evaluated using the backend's accepted civil-time/timezone rules, not browser clock inference.

## 7. Frontend responsibilities

Frontend may:
- validate and normalize shareable URL navigation state;
- omit default values from the URL for compact canonical navigation;
- call the repository from the route loader so primary inventory is SSR-renderable;
- render static Persian labels/descriptions and localize enum labels;
- format offset-aware timestamps using the supplied timezone;
- render filter chips, pagination and empty/error/retry states;
- link tournament items to stable `/tournaments/{slug}` detail routes;
- use a deterministic fixture repository in dev/test/visual QA only;
- apply its own SEO canonical/robots policy to faceted URL variants.

Frontend MUST NOT:
- authoritatively filter/sort production results after download;
- infer lifecycle, registration availability, venue verification or capacity from browser-only data;
- choose a featured tournament from local heuristics when the contract does not supply one;
- fabricate counts, venue verification, fee/prize or inventory records if the endpoint fails;
- build relations from visible names.

## 8. HTTP / public-safety behavior

Future implementation requirements:
- anonymous-safe `GET` only;
- no side effects;
- success: `200` with runtime-valid response envelope;
- page beyond the last available page must resolve under an explicitly tested API policy (empty valid page or typed invalid-page response) rather than browser guesswork;
- malformed/unsupported query receives typed validation behavior; frontend fallbacks never replace backend validation;
- temporary failure remains an unavailable/error state and does not authorize fixture fallback in production.

The projection MUST NOT expose:
- phone/email/private account fields;
- payment/refund/settlement details;
- roles/permissions;
- moderation/dispute evidence;
- private challenge/team data;
- any field not approved for anonymous public display by its owning domain.

## 9. Relationship to existing contracts

- F16 Home may navigate into this endpoint's accepted query values but does not own their runtime semantics.
- F01 tournament detail/registration remains the authority for one tournament's complete detail and participation commands.
- future Games/Catalog owns canonical game identities/slugs.
- future Gaming Centers owns center identity/verification/location.
- future Tournaments/Registrations owns tournament lifecycle, registration state, capacity, fee/prize and inventory membership.

No contract here weakens those domain boundaries.

## 10. SEO / faceted URL boundary

SEO/indexing policy is frontend/search-engine presentation responsibility, not backend business truth. The API accepts useful filter URLs for users even when the frontend marks filtered variants non-indexable/canonicalizes them to the base inventory URL.

The backend contract therefore does not create SEO landing-page semantics for arbitrary facet combinations.

## 11. Phase boundary

F17 contract alignment does NOT add:
- Python code;
- models or migrations;
- serializers/views/URLs;
- tournament/registration business logic;
- gaming-center verification logic;
- dependencies;
- `docs/PHASE_REGISTRY.md` changes.

Owning domains must be implemented in accepted phase order with their own Issues, tests, CI, PRs and closeouts. The endpoint becomes live only when its dependencies exist and the tournaments/registrations phase explicitly implements and tests it.
