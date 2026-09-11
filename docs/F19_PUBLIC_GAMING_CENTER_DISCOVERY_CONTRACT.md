# F19 — Public Gaming Center Discovery Contract Alignment

Status: `IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/centers`

Frontend workstream: `F19 — Public Gaming Center Discovery`

Frontend tracking Issue: `sajadkhavas/turnoment#92`

Backend tracking Issue: `#35`

Backend START_SHA:

`b0fc9ed73dc57aed6a28453745386489aaef0ceb`

Runtime truth:

`FRONTEND MOCK / BACKEND PENDING`

Backend NEXT:

`P02 — Games / Catalog Foundation`

## 1. Purpose

Freeze the public gaming-center directory ownership/projection contract so frontend F19 can use a permanent production adapter without making local arrays authoritative for center publication, verification, locality, facilities, tournament counts, filtering or pagination.

This document does not implement an endpoint and does not start/reorder the future gaming-centers/resources backend phase.

## 2. Planned endpoint

`GET /api/v1/centers/`

Optional query parameters:
- `city=<stable-city-slug>`;
- `page=<positive-integer>`.

Properties when the owning backend phase eventually implements it:
- read-only;
- anonymous-safe;
- explicitly opts into `AllowAny` because Turnoment global permission defaults remain authenticated;
- validation and filtering remain backend-authoritative;
- no private account/contact/permission/payment/moderation information may be emitted.

DRF official permission guidance confirms permission checks run before view code and `AllowAny` explicitly permits unauthenticated access. Existing Turnoment `/api/v1/` API versioning law remains unchanged.

## 3. Response projection

```text
schemaVersion: 1
filters:
  cities[]
    cityId
    slug
    name
    count
activeQuery:
  city: stable city slug | omitted
  page: positive integer
items[]
  centerId
  publicId
  publicationState: published
  name
  verified
  city:
    cityId
    slug
    name
  district
  summary
  equipmentLabels[]
  coverImage: string | null
  upcomingTournamentCount: non-negative integer | null
pagination:
  currentPage
  totalPages
  totalItems
  pageSize
```

## 4. Identity and future detail-route boundary

`centerId` is the stable backend relation/entity key.

`publicId` is the frontend navigation key supplied for the currently reserved public detail route. F19 uses it only to preserve navigation compatibility.

The later `/centers/$id` frontend recertification owns the final public canonical identifier/slug decision. This F19 contract MUST NOT silently force the later detail route to keep an opaque ID forever. If the later workstream adopts a canonical slug, backend contract evolution must keep redirects/identity migration controlled and explicit.

Display names are never relation keys.

## 5. Publication, verification and locality

The backend owns:
- whether a center is present in the public directory;
- public ordering;
- authoritative verification state;
- stable city identity and slug;
- district/locality text appropriate for the public directory.

The frontend MUST NOT infer verification or directory membership from local tournament records.

City facet counts and filtering are backend projections. The frontend may normalize URL search input, but it does not recreate production city membership or counts from a local full-center array.

## 6. Facilities and tournament-count truth

`equipmentLabels[]` are public facility/equipment labels owned by the center domain and projected by the backend. Duplicate labels for one center are invalid.

`upcomingTournamentCount` is nullable:
- integer `0+` = authoritative projected count;
- `0` = authoritative zero;
- `null` = authoritative count unavailable/not projected.

The frontend must use neutral copy for `null` and MUST NOT derive a replacement count from local tournament arrays.

## 7. Ratings/reviews deliberately excluded

F19 v1 public list projection has no `rating` or `reviews` fields.

Reason: the current accepted backend plan has no implemented/reviewed ratings domain with authoritative aggregation semantics, abuse controls or publication policy. The frontend must not display fabricated/local review metrics as production truth.

A future ratings/reviews feature requires its own domain contract and authorization/integrity decisions before these fields can be introduced.

## 8. Pagination integrity

For the returned projection:
- `currentPage >= 1`;
- `pageSize >= 1`;
- `totalItems >= 0`;
- `totalPages = max(1, ceil(totalItems / pageSize))`;
- `currentPage <= totalPages`;
- returned `items.length <= pageSize`;
- stable center IDs/public IDs are unique within one page;
- stable city IDs/slugs are unique within the facet list.

Empty filtered inventory is a valid state and must not trigger fabricated production fallback records.

## 9. Ownership split

Backend/repository owns:
- published center membership/order;
- stable center ID and public navigation key projection;
- name;
- verification;
- city/district identity;
- center summary;
- equipment labels;
- cover image URL;
- optional authoritative upcoming-tournament count;
- city facets/counts;
- filtering;
- pagination.

Frontend owns:
- safe normalization/shareability of `city` and `page` URL state;
- final Persian page copy/information hierarchy;
- presentation/formatting;
- accessibility/responsive behavior;
- canonical `/centers` and robots policy;
- crawlable navigation to center detail and related tournament/game discovery;
- deterministic fixture data for dev/test/visual QA only.

## 10. Production adapter behavior

Frontend production adapter targets `GET /api/v1/centers/` and runtime-validates the strict payload.

Production MUST fail closed when:
- API base URL is missing;
- HTTP response is unsuccessful;
- payload violates the contract.

Production MUST NOT silently replace failures with fixture centers.

## 11. Security / privacy

The public directory response must not contain:
- phone/email unless a later explicitly accepted public-contact contract authorizes specific fields;
- private account/profile data;
- staff/group/permission internals;
- moderation evidence/private verification documents;
- payment/refund/settlement data;
- secrets or operational configuration.

Verification is a public state projection only; its private evidence remains non-public.

## 12. Phase-order guard

Backend phase registry remains authoritative:

`P02 — Games / Catalog Foundation`

is still NEXT. Gaming centers/resources implementation comes after the accepted games/catalog phase order.

F19 docs alignment must not modify `docs/PHASE_REGISTRY.md`, add center models/migrations, or introduce views/serializers/URLs ahead of the owning runtime phase.

## 13. Documentation-only boundary

This alignment may change only:
- `PROJECT_CONTINUITY.md`;
- `docs/F19_PUBLIC_GAMING_CENTER_DISCOVERY_CONTRACT.md`.

Forbidden here:
- Python;
- models/migrations;
- serializers/views/URLs;
- settings/dependencies;
- `docs/PHASE_REGISTRY.md`;
- phase reordering.

Closing backend Issue #35 means the cross-repo contract documentation is aligned. It does not mean `GET /api/v1/centers/` is live.
