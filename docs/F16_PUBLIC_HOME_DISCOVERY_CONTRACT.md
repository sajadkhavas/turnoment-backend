# F16 — Public Home Discovery Contract

Status: `PLANNED CONTRACT / FRONTEND MOCK / BACKEND PENDING`

Frontend route: `/`

Backend owner: cross-domain public discovery projection composed from games, tournaments/registrations, gaming centers and rankings/matches when those owning phases exist.

Planned endpoint:

`GET /api/v1/discovery/home/`

This document defines the stable frontend-facing projection only. It does not authorize runtime implementation or reorder backend phases. Backend NEXT remains exactly `P02 — Games / Catalog Foundation`.

## 1. Purpose

The Home route is a broad discovery gateway, not an authoritative domain owner. It needs one SSR-friendly anonymous projection so public content can be rendered from typed server truth without duplicating business logic in the browser.

The endpoint may aggregate only already-authoritative domain values. It MUST NOT create independent Home-only truth for verification, lifecycle, capacity, ranking, result or rating.

## 2. Response envelope

```text
schemaVersion
stats?
  activeGamingCenters
  openOrUpcomingTournaments
  registeredPlayers
finder
  games[]
    gameId
    slug
    name
  cities[]
    value
    label
  dateBuckets[]
    value       # today | tomorrow | weekend | week
    label
popularGames[]
  gameId
  slug
  name
  platformLabel
  imageUrl
  activeTournamentCount
featuredTournaments[]
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
  startsAt
  timezone
  formatLabel
  capacity
  registeredCount
  entryFee
  fixedPrize
  registrationState
  lifecycleState
featuredGamingCenters[]
  gamingCenterId
  name
  verified
  rating?
  reviewCount?
  city
  district
  imageUrl
  equipmentLabels[]
  upcomingTournamentCount
rankingPreview?
  game
    gameId
    slug
    name
  entries[]
    rank
    player
      playerId
      username
      gamerTag
    city?
    rating
    finalizedMatches
    wins
    trend       # up | down | flat
featuredShowdown?
  tournamentId?
  tournamentSlug?
  matchId?
  eyebrow
  title
  subtitle
  startsAt
  timezone
  venueName
  playerA
    playerId
    username
    gamerTag
    city?
    rating
    recordLabel?
  playerB
    playerId
    username
    gamerTag
    city?
    rating
    recordLabel?
```

`stats`, `rankingPreview` and `featuredShowdown` are optional because absence is safer than fabricated or stale public claims.

## 3. Authoritative enums

`registrationState`:
- `open`
- `filling`
- `closed`
- `unavailable`

`lifecycleState`:
- `upcoming`
- `live`
- `completed`
- `cancelled`

Finder date buckets are navigation hints only:
- `today`
- `tomorrow`
- `weekend`
- `week`

The detailed `/tournaments` endpoint remains authoritative for filter semantics and current inventory.

## 4. Integrity rules

- stable IDs/slugs are required for all relations/navigation; display labels are never relation keys;
- `registeredCount <= capacity` whenever capacity is finite;
- a featured tournament cannot be `completed` or `cancelled` when presented as upcoming registration inventory;
- `registrationState=open|filling` requires lifecycle compatible with future participation;
- `verified` is backend-owned and never inferred from presence in the Home list;
- ranking values are authoritative projections from the ranking/results owners; frontend does not compute rank, rating, wins or trend;
- optional showdown must come from authoritative competition/match/result context and must not expose a fabricated winner or rating delta;
- aggregate stats are returned only if the backend can compute them authoritatively at request time or from an accepted aggregate projection;
- empty arrays are valid and must not be replaced by fake production records.

## 5. Privacy / public-safety rules

This endpoint is anonymous-safe and MUST NOT expose:
- phone or email;
- private account/profile fields;
- group/permission data;
- payment/refund/settlement data;
- moderation/dispute evidence;
- private Challenge data;
- any field not already approved for public display by its owning domain.

Public player identities use only fields allowed by the public player projection.

## 6. Frontend responsibilities

Frontend may:
- render final Persian copy and visual hierarchy;
- format offset-aware `startsAt` values in the supplied IANA timezone;
- keep temporary finder form state;
- navigate to `/tournaments` using validated search values;
- link to stable game/tournament/center/player routes;
- hide optional sections when projection data is absent;
- use a deterministic fixture repository only in dev/test/visual QA.

Frontend MUST NOT:
- calculate verification, capacity truth, lifecycle, ranking/rating or result truth;
- derive backend-owned values from timestamps or list lengths;
- display fixture data as a production fallback when the Home endpoint fails;
- create relationships from display names.

## 7. HTTP behavior

Future implementation requirements:
- anonymous safe `GET` only;
- no side effects;
- successful response: `200` with the runtime-validated projection;
- malformed query is not applicable because the initial endpoint has no required query parameters;
- temporary backend failure remains an error/unavailable state; it does not authorize synthetic production content.

Caching policy must be decided by the runtime implementation based on freshness requirements of tournament capacity/lifecycle and ranking data. The frontend may use router-level caching only if it does not misrepresent freshness-sensitive business truth.

## 8. Phase boundary

F16 contract alignment does NOT add:
- Python code;
- models or migrations;
- serializers/views/URLs;
- ranking, tournament, center or match business logic;
- phase-registry changes.

Owning backend domains must be implemented in accepted phase order with their own Issues, tests, CI, PRs and closeouts. The Home projection becomes live only when those dependencies are available and the aggregation endpoint is implemented under an authorized backend phase.
