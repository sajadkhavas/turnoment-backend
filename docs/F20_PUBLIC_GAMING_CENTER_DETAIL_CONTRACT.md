# F20 — Public Gaming Center Detail Contract Alignment

Status: `IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/centers/$id`

Frontend workstream: `F20 — Public Gaming Center Detail`

Frontend tracking Issue: `sajadkhavas/turnoment#95`

Backend tracking Issue: `#37`

Backend START_SHA:

`b6421e1e76e846c89d799fe4860bc11c8242f2f8`

Runtime truth:

`FRONTEND MOCK / BACKEND PENDING`

Backend NEXT:

`P02 — Games / Catalog Foundation`

## 1. Purpose

Freeze the future public gaming-center detail ownership/projection required by frontend F20 without starting or reordering the gaming-centers/resources runtime backend phase.

This document does not implement an endpoint. It records the contract the later owning backend phase must satisfy.

## 2. Planned endpoint

`GET /api/v1/centers/{publicId}/`

Future endpoint properties:
- read-only;
- anonymous-safe only for a center that is public/published;
- explicitly opts into `AllowAny` under Turnoment's authenticated global permission default;
- validates the path identifier server-side;
- fails closed for unknown, unpublished or non-public center detail;
- returns a strict public projection with no private business/operator data.

## 3. Identity / canonical-route decision

F20 v1 uses `publicId` as the canonical public route identifier.

Identity split:
- `centerId` = stable backend relation/entity key;
- `publicId` = stable public navigation/canonical-route identifier for F20 v1;
- `name` = display value only and never a relation key.

Reasoning:
- frozen frontend F19 already links `/centers/{publicId}`;
- keeping `publicId` avoids reopening frozen F19 solely for an identifier migration;
- the old local implementation's display-name tournament join is explicitly rejected;
- any future human-readable slug migration requires an explicit alias/redirect/versioned compatibility contract.

The endpoint response `publicId` must represent the same authoritative public identity resolved from the request.

## 4. Response projection

```text
schemaVersion: 1
centerId
publicId
publicationState: published
name
verified
city
  cityId
  slug
  name
district
summary
description
equipmentLabels[]
coverImage: string | null
galleryImages[]
upcomingTournamentCount: non-negative integer | null
publicAddress: object | null
  streetAddress
  addressLocality
  addressRegion: string | null
  postalCode: string | null
  addressCountry: IR
  displayAddress
publicPhone: string | null
openingHours[]
  dayOfWeek[]
  opens
  closes
mapUrl: string | null
tournaments[]
  tournamentId
  tournamentSlug
  title
  game
    gameId
    slug
    name
  startsAt
  displayDate
  displayTime
  registrationState
```

The frontend may derive static final SEO title/description wording from these authoritative identity/locality fields. The backend does not own presentation copy.

## 5. Publication / verification truth

Backend owns:
- whether the center is public/published;
- stable center identity;
- public identity projection;
- public verification state;
- public city/district identity;
- public summary/description;
- public facilities/media projection.

`verified` is only a public state value. The endpoint never exposes the private evidence or moderation workflow used to establish that state.

## 6. Public visit-information policy

`publicAddress`, `publicPhone`, `openingHours` and `mapUrl` are public projections, not raw owner/account fields.

They may be emitted only when the owning center domain explicitly authorizes them for public display.

### Address

When non-null, `publicAddress` contains:
- `streetAddress`;
- `addressLocality`;
- nullable `addressRegion`;
- nullable `postalCode`;
- `addressCountry = IR`;
- user-facing `displayAddress` consistent with the structured fields.

A missing address is valid. The frontend must not infer one from city/district or local fixture data.

### Phone

`publicPhone` is nullable. A private owner/operator account number must not become public merely because it exists in the database. The domain must deliberately mark/project the business contact as public.

### Opening hours

Each public opening-hours record contains:
- one or more unique weekdays;
- `opens` as 24-hour local civil time;
- `closes` as 24-hour local civil time.

The same weekday must not be represented by conflicting records in one projection.

### Map URL

`mapUrl` is optional and must be a validated public URL when present. It is not a substitute for authoritative address truth.

## 7. Facilities / media

`equipmentLabels[]` are backend-owned public labels. Duplicate labels are invalid.

`coverImage` is nullable.

`galleryImages[]` is a bounded public gallery projection; duplicate image URLs are invalid.

The endpoint exposes only media authorized for public display and never private verification uploads.

## 8. Tournament projection

The detail page may receive a bounded projection of public upcoming/relevant tournaments belonging to the center.

Each item uses:
- stable `tournamentId`;
- canonical `tournamentSlug`;
- public title;
- stable game identity + canonical game slug;
- authoritative start datetime;
- public display date/time projection;
- authoritative registration state.

The backend relation is by stable center identity, not center display name.

`upcomingTournamentCount` semantics:
- `null` = authoritative count unavailable/not projected;
- `0` = authoritative zero;
- positive integer = authoritative count.

Integrity:
- authoritative zero cannot coexist with projected upcoming tournament items;
- when the count is non-null it cannot be lower than the number of tournaments returned in the bounded projection;
- tournament IDs/slugs are unique in the response.

The frontend must not reconstruct a replacement count from local arrays.

## 9. Ratings/reviews explicitly excluded

F20 v1 contains no:
- rating;
- review count;
- aggregate rating;
- review text.

Reason: no accepted ratings domain currently defines authoritative aggregation, abuse handling and publication semantics.

A future ratings feature requires its own domain and contract review before any rating/review field or structured-data markup is added.

## 10. LocalBusiness structured-data boundary

Google `LocalBusiness` markup is a frontend/search presentation concern, but its values must come from this authoritative public projection.

The frontend may emit generic `LocalBusiness` JSON-LD only when:
- `publicAddress` is non-null and complete enough for the markup;
- the same address is visible to the user on the page;
- any telephone/opening-hours values included are also public-authorized and visible;
- no unsupported rating/review markup is added.

Mapping:
- `name` ← public center name;
- `PostalAddress.streetAddress` ← `publicAddress.streetAddress`;
- `addressLocality` ← `publicAddress.addressLocality`;
- optional region/postal code from public address;
- `addressCountry` ← `IR`;
- optional `telephone` ← `publicPhone`;
- optional `openingHoursSpecification` ← `openingHours`;
- optional image only from public HTTP(S) media.

If `publicAddress` is null, the frontend omits LocalBusiness markup rather than inventing data.

## 11. Security / privacy

The public detail response must not contain:
- private owner/operator phone or email unless deliberately projected as public business contact;
- private account/profile identifiers;
- groups/permissions/staff internals;
- verification documents or evidence;
- moderation reports/evidence;
- payment/refund/settlement data;
- private notes;
- credentials, secrets or operational configuration.

Publication/permission checks remain server-side authoritative even when the frontend runtime-validates the JSON response.

## 12. Failure / not-found behavior

When eventually implemented:
- unknown `publicId` → public not-found response;
- unpublished/non-public center → must not leak private existence/detail through the public projection;
- invalid path identity → validation/not-found behavior according to owning API implementation;
- server/contract failures fail closed;
- no fixture/demo fallback is a production behavior.

The frontend maps a public 404 to its final not-found page and treats other HTTP/contract failures as retryable error state without exposing raw server errors.

## 13. Ownership split

Backend/repository owns:
- publication membership and identity;
- `centerId`/`publicId` truth;
- verification;
- locality;
- summary/description domain content;
- public visit/contact/hours/map projection;
- equipment/media;
- authoritative tournament relationship/projection/count;
- privacy/publication policy.

Frontend owns:
- route presentation;
- final natural Persian copy around authoritative data;
- title/meta/canonical/robots;
- conditional LocalBusiness markup using only authoritative public values;
- accessibility/responsive behavior;
- links to directory/tournament/game routes;
- deterministic fixture data for dev/test/visual QA only.

## 14. Production adapter behavior

Frontend production adapter targets:

`GET /api/v1/centers/{publicId}/`

Frontend production behavior must:
- require configured API base URL;
- send read-only GET;
- use same-session-compatible credentials policy;
- map 404 to not-found;
- reject unsuccessful non-404 responses;
- runtime-validate the strict payload;
- verify returned `publicId` matches requested identity;
- never silently fall back to fixtures.

## 15. Phase-order guard

Backend phase registry remains authoritative.

NEXT remains:

`P02 — Games / Catalog Foundation`

F20 documentation alignment must not:
- add Python;
- add models/migrations;
- add serializers/views/URLs;
- change dependencies/settings/workflows;
- modify `docs/PHASE_REGISTRY.md`;
- start gaming-centers/resources runtime implementation before the accepted sequence reaches it.

## 16. Documentation-only boundary

This alignment may change exactly:
- `PROJECT_CONTINUITY.md`;
- `docs/F20_PUBLIC_GAMING_CENTER_DETAIL_CONTRACT.md`.

Closing backend Issue #37 means the cross-repo contract documentation is aligned. It does **not** mean the detail endpoint is live.
