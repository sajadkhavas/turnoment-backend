# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-12`

## 1. Continuation law

Every backend chat/agent MUST:
1. read this file and `PHASE_COMPLETION_PROTOCOL.md`;
2. verify exact current `main` before mutation;
3. read `docs/PHASE_REGISTRY.md` before starting/reordering a backend phase;
4. use a dedicated branch/Issue/PR;
5. never claim DONE from chat memory;
6. keep cross-repo frontend contracts explicit without pretending planned APIs are live;
7. preserve exact SHA/CI/PR/Issue evidence;
8. obey `docs/ENGINEERING_RULES.md`, including explicit `AllowAny` for future public endpoints under the authenticated global default;
9. keep docs-only alignment work out of Python/models/migrations/serializers/views/URLs/settings/dependencies/phase-registry;
10. keep runtime phase order authoritative even when frontend architecture is frozen first.

## 2. Current backend truth

Repository: `sajadkhavas/turnoment-backend`

Current live backend `main` / F20 documentation-alignment START_SHA:

`b6421e1e76e846c89d799fe4860bc11c8242f2f8`

P00 and P01 remain terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry still orders runtime work as games/catalog first, then gaming centers/resources, then tournaments/registrations, rankings and later competitive slices. Cross-repo documentation alignment MUST NOT reorder that sequence.

Current runtime truth for F20 remains:

`FRONTEND MOCK / BACKEND PENDING`

## 3. Accepted F19 Public Gaming Center Discovery alignment

F19 documentation alignment is terminal as documentation-only work:
- backend Issue `#35` — CLOSED / COMPLETED;
- branch `docs/f19-public-gaming-center-discovery-contract`;
- docs head `7f2663fa649df9b17bd2d5282e497954cb277359`;
- PR `#36` — MERGED;
- backend merge/main `b6421e1e76e846c89d799fe4860bc11c8242f2f8`;
- PR-context Backend Quality Gate `34641469931` — PASS on Python 3.12 / 3.14;
- post-main Backend Quality Gate `34641761119` — PASS on Python 3.12 / 3.14;
- no gaming-center runtime Python/model/migration/serializer/view/URL/settings/dependency/phase-registry implementation was added.

Accepted F19 planned endpoint:

`GET /api/v1/centers/`

F19 established:
- `centerId` as stable backend relation/entity identity;
- `publicId` as public navigation-key projection;
- display names are never relation keys;
- backend-owned public membership/order/verification/locality/facilities/count/filter/pagination truth;
- no rating/review projection without a separately accepted ratings domain;
- public list response excludes private contact/account/verification-evidence/payment/moderation data;
- production frontend must fail closed without fixture fallback.

## 4. Active cross-repo alignment — F20 Public Gaming Center Detail

Frontend repository: `sajadkhavas/turnoment`.

Frontend route:

`/centers/$id`

Frontend F20 START_SHA:

`a473613191fd5132664c5234b692befda4a5cf41`

Frontend tracking Issue:

`sajadkhavas/turnoment#95`

Backend tracking Issue:

`#37`

Backend docs branch:

`docs/f20-public-gaming-center-detail-contract`

Contract source:

`docs/F20_PUBLIC_GAMING_CENTER_DETAIL_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Planned endpoint:

`GET /api/v1/centers/{publicId}/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. F20 canonical identity truth

F20 v1 keeps the already-projected `publicId` as the canonical public detail-route identifier.

Reasons:
- frozen F19 `/centers` already links to `/centers/{publicId}`;
- `centerId` remains the stable backend relation key;
- display names are not keys;
- F20 does not reopen frozen F19 solely to perform an SEO slug migration;
- a future human-readable slug migration requires an explicit alias/redirect/versioned contract and controlled compatibility work.

The backend MUST resolve the requested `publicId` to the authoritative published center without treating the display name as identity.

## 6. F20 planned public detail projection

Planned response:

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

Projection invariants:
- only public/published center detail may be returned by the anonymous public endpoint;
- response `publicId` must match the resolved canonical public identity;
- duplicate equipment/gallery/tournament identities are invalid;
- `upcomingTournamentCount = 0` means authoritative zero and cannot coexist with projected upcoming tournaments;
- when count is non-null it cannot be smaller than the returned bounded tournament projection;
- tournament relations use stable tournament IDs/slugs, never center display-name joins;
- offset-aware tournament datetimes remain backend-owned truth.

## 7. Public visit-information policy

The detail endpoint may expose visit information only when the center/domain explicitly authorizes those values for public display.

Allowed when public-authorized:
- physical public address;
- public phone number;
- public opening hours;
- public map URL.

Forbidden:
- private owner/operator phone/email unless separately approved as the public business contact;
- private account/profile identifiers;
- groups/permissions/staff internals;
- verification documents/evidence;
- moderation evidence;
- payment/refund/settlement data;
- secrets or operational configuration.

Missing public address/phone/hours is a valid state. The frontend must not fabricate replacements.

## 8. Ratings/reviews policy

F20 v1 contains no rating, review count, aggregate rating or review text.

The current backend roadmap has no accepted public ratings domain with aggregation, abuse controls and publication semantics. These fields therefore remain excluded from the detail contract and from structured data.

## 9. LocalBusiness structured-data boundary

Frontend may emit a generic `LocalBusiness` JSON-LD projection only when the F20 response includes a complete authoritative `publicAddress` that is also visible on the page.

Allowed structured-data mapping when authoritative:
- business `name`;
- `PostalAddress` from public address fields;
- optional public `telephone`;
- optional public opening-hours specifications;
- optional public HTTP(S) image.

Forbidden:
- invented address/contact/hours;
- aggregateRating/review markup without an accepted ratings domain;
- private verification/account data.

If public address is absent, LocalBusiness markup is omitted rather than guessed.

## 10. Permissions / API rules

When its owning runtime phase eventually implements the endpoint:
- route remains under `/api/v1/`;
- public read access must explicitly opt into `AllowAny` because Turnoment global permissions remain authenticated;
- validation and publication checks remain server-side authoritative;
- unpublished/private/non-public center detail must fail closed as not publicly available;
- no frontend route guard or Zod validation replaces backend validation/authorization/publication policy.

## 11. Official-source decisions

Reviewed before F20 documentation mutation:
- root `PHASE_COMPLETION_PROTOCOL.md`;
- `docs/PHASE_REGISTRY.md`;
- `docs/ENGINEERING_RULES.md`;
- `docs/FRONTEND_BACKEND_CONTRACT.md`;
- accepted F19 gaming-center discovery contract;
- Django REST framework permission/versioning rules already governing public `/api/v1/` projections.

Applied decisions:
- future public endpoint requires explicit `AllowAny`;
- F20 contract reuses F19 center identity instead of display-name joins;
- public contact fields require explicit publication semantics;
- detail contract does not start the gaming-centers runtime phase before P02.

## 12. Previous accepted alignment chain

Accepted documentation-only alignments remain recorded in their Issues/PRs:
- F14 — Issue #25 / PR #26;
- F15 — Issue #27 / PR #28;
- F16 — Issue #29 / PR #30;
- F17 — Issue #31 / PR #32;
- F18 — Issue #33 / PR #34, backend main `b0fc9ed73dc57aed6a28453745386489aaef0ceb`;
- F19 — Issue #35 / PR #36, backend main `b6421e1e76e846c89d799fe4860bc11c8242f2f8`.

None of these frontend contract freezes reorders backend runtime phases.

## 13. Exact F20 backend alignment NEXT

1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F20_PUBLIC_GAMING_CENTER_DETAIL_CONTRACT.md` from backend START `b6421e1e76e846c89d799fe4860bc11c8242f2f8`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #37;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend main lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend main;
10. record terminal documentation-alignment evidence in Issue #37 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`;
12. continue to describe runtime truth as `FRONTEND MOCK / BACKEND PENDING` until the owning runtime phase actually ships.
