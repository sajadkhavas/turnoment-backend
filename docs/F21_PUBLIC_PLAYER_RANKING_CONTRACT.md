# F21 — Public Player Ranking Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/ranking`

Frontend tracking Issue: `sajadkhavas/turnoment#98`

Backend tracking Issue: `#39`

Backend START_SHA:

`e8e48061cba201b3a12ac534ef97f22565bea5a3`

Frontend F21 START_SHA:

`b585e1e421c2e0febedf53e43349a23666004338`

Frontend source checkpoint used for this alignment:

`2d75596a31440dcd795ea609926a02e7a478e71e`

## 1. Scope and phase-order law

This file aligns the future backend ranking contract with the frontend F21 architecture. It does **not** implement ranking runtime code and does not reorder backend phases.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry still orders runtime work through games/catalog, gaming centers/resources, tournaments/registrations and only then rankings/competitive slices. F21 documentation alignment does not change that order.

Runtime remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

## 2. Planned public endpoint

`GET /api/v1/rankings/`

Planned query parameters:
- `game=<stable-game-slug>`;
- `season=<stable-season-slug>`;
- `region=<stable-region-slug>`;
- `type=tournament|challenge`;
- `page=<positive-integer>`.

The eventual endpoint is read-only and anonymous-safe only for public ranking projections.

## 3. Authority boundary

Backend eventually owns:
- leaderboard membership;
- authoritative ordering/rank;
- stable `playerId` relation identity;
- public `username` navigation identity;
- public gamer tag;
- stable game and city identity;
- Tournament Rating and Challenge Rating truth;
- selected rating projection for the requested ranking type;
- match-record projection;
- rank movement;
- game/season/region/type facet membership and normalization;
- filtering;
- deterministic pagination.

Frontend owns:
- runtime-validated/shareable URL search state;
- presentation and final public copy;
- title/meta/canonical/robots;
- accessibility/responsive behavior;
- deterministic dev/test/visual-QA fixtures behind the same typed contract.

Frontend must never calculate official rank, rating, movement or challenge eligibility.

## 4. Rating-domain rule

Tournament Rating and Challenge Rating are separate competitive truths.

For F21 v1, each ranking row contains one authoritative `rating` paired with an explicit `ratingType`. Changing `type` requests a different backend-owned leaderboard projection; the browser does not derive one rating from the other.

F21 v1 does not require public challenge-eligibility fields in ranking rows. Eligibility remains backend-owned and may be added only through a separately accepted contract when the owning runtime domain is ready.

The platform's existing challenge-unlock rule is not recalculated by the ranking frontend.

## 5. Planned response projection

```text
schemaVersion: 1
filters
  games[]
    gameId
    slug
    name
  seasons[]
    id
    slug
    label
  regions[]
    id
    slug
    label
  types[]
    id: tournament | challenge
    label
activeQuery
  game
  season
  region: slug | omitted
  type: tournament | challenge
  page
items[]
  playerId
  username
  gamerTag
  city
    cityId
    slug
    name
  game
    gameId
    slug
    name
  rank
  rating
  ratingType: tournament | challenge
  played
  wins
  losses
  draws
  movement
    direction: up | down | flat
    positions
pagination
  currentPage
  totalPages
  totalItems
  pageSize
```

## 6. Identity and integrity rules

- `playerId` is the stable backend relation identity.
- `username` is the public profile-navigation identity when the player is publicly projectable.
- `gamerTag` is display text and is never a relation key.
- game/city/facet slugs are stable public query identities; display labels are not keys.
- page player IDs and usernames must be unique.
- projected ranks on a page must be unique and ordered ascending.
- every row must match the authoritative active game.
- every row's `ratingType` must match the active ranking type.
- wins + losses + draws must equal the projected played count under this contract.
- flat movement has zero positions; up/down movement has a positive position count.
- pagination counts must be internally consistent.
- deterministic authoritative ordering must be applied **before** pagination.

The eventual backend may enforce stronger domain/database invariants when ranking storage and calculation are implemented.

## 7. Filtering and invalid-query behavior

The backend owns domain validation for game/season/region/type values. Frontend syntax validation does not replace backend validation.

Unknown or unsupported filter identities must not silently select unrelated data. The eventual endpoint should return a deliberate validation/not-found style API outcome according to the owning ranking API design.

Filtering must be applied server-side before pagination and before the public projection is serialized.

## 8. Pagination decision

F21 uses page-number navigation because the public UI exposes numbered current/total pages and the current contract uses `page=<positive-integer>`.

Current DRF pagination guidance supports `PageNumberPagination` for this pattern. The implementation phase must define a deterministic ordering appropriate to ranking truth before pagination so users do not receive unstable/duplicate/missing ranks between page requests.

Client-controlled arbitrary ordering is not part of F21 v1.

## 9. Permissions and privacy

Turnoment's global API permission policy is authenticated. When the owning runtime phase implements this public endpoint, it must explicitly opt into:

`AllowAny`

for the read-only public ranking projection.

Public ranking responses may contain only public-safe competitive identity/statistics. They must exclude:
- private phone/email;
- authentication/session/OTP data;
- staff/group/permission internals;
- moderation evidence;
- verification documents;
- payment/refund/settlement data;
- secrets/configuration;
- private account/profile fields not accepted for public projection.

A frontend link to `/players/{username}` does not authorize additional player data; the future player-detail endpoint remains responsible for its own privacy projection.

## 10. Publication / competitive truth

Only players/results eligible for the public leaderboard under the future ranking domain may contribute to public ranking truth.

The eventual backend owns decisions around:
- finalized/valid result inclusion;
- rating calculation/versioning;
- season boundaries;
- region membership;
- tie-breaking;
- movement baseline/comparison period;
- ranking eligibility/publication.

F21 frontend deliberately treats these as opaque authoritative outputs rather than formulas.

## 11. Official DRF documentation decisions

Reviewed before this documentation alignment:
- DRF Permissions — permission checks happen before view execution; `AllowAny` explicitly communicates unrestricted public access;
- DRF Filtering — filtering/restriction belongs server-side and may be implemented through querysets/filter backends;
- DRF Pagination — page-number pagination supports a `page` query parameter and requires attention to deterministic ordering.

Applied contract decisions:
- future public ranking endpoint explicitly opts into `AllowAny`;
- accepted query dimensions are validated server-side;
- deterministic ranking order is established before pagination;
- no arbitrary client ordering is authorized in F21 v1;
- documentation alignment does not start the rankings runtime phase.

## 12. Frontend SEO/indexing relationship

Backend does not own frontend indexing directives, but its contract supports the accepted frontend policy:
- base `/ranking` canonical/indexable;
- game/season/region/type/page variants are current navigation states, `noindex,follow`, canonical `/ranking`;
- no unsupported national/official-ranking claim;
- no ranking structured data is inferred from backend fields merely for schema coverage.

## 13. Documentation-alignment acceptance

This alignment may change exactly two Markdown files:
1. `PROJECT_CONTINUITY.md`;
2. `docs/F21_PUBLIC_PLAYER_RANKING_CONTRACT.md`.

It must not change Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows or `docs/PHASE_REGISTRY.md`.

Required evidence before closing backend Issue #39:
- one docs commit / two Markdown files / ahead 1 / behind 0;
- Backend Quality Gate PASS on Python 3.12 and 3.14;
- docs PR-context gate PASS;
- mergeable=true;
- unresolved review threads=0;
- exact pre-merge backend main lock;
- expected-head merge;
- post-main Backend Quality Gate PASS;
- exact live backend main verification;
- terminal evidence in Issue #39 and close `completed`.
