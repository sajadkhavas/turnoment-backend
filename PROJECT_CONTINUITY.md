# TURNOMENT — BACKEND PROJECT CONTINUITY CHECKPOINT

> **MANDATORY FIRST READ FOR EVERY CHAT / AGENT / SESSION**

Last checkpoint update: `2026-09-11`

## 1. Continuation law

Every backend chat/agent MUST:
1. read this file and `PHASE_COMPLETION_PROTOCOL.md`;
2. verify exact current `main` before mutation;
3. read `docs/PHASE_REGISTRY.md` before starting/reordering a backend phase;
4. use a dedicated branch/Issue/PR;
5. never claim DONE from chat memory;
6. keep cross-repo frontend contracts explicit without pretending planned APIs are live;
7. update continuity/evidence before ending;
8. preserve exact SHA/CI/PR/Issue evidence;
9. obey `docs/ENGINEERING_RULES.md`, including public `AllowAny` opt-in and server-side validation/authorization;
10. keep docs-only alignment work out of Python/models/migrations/serializers/views/URLs/dependencies/phase-registry unless an authorized runtime phase explicitly starts.

## 2. Current backend repository truth

Repository: `sajadkhavas/turnoment-backend`

Current accepted backend `main` / F19 docs-alignment START_SHA:

`b0fc9ed73dc57aed6a28453745386489aaef0ceb`

This is the merged F18 Public Game Catalog documentation-alignment main.

P00 and P01 remain terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry still orders domain implementation as games/catalog first, then gaming centers/resources, then tournaments/registrations, rankings and later competitive slices. Cross-repo frontend contract alignment MUST NOT reorder that sequence.

Runtime truth for frontend surfaces whose owning backend phase has not shipped remains:

`FRONTEND MOCK / BACKEND PENDING`

## 3. Active cross-repo alignment — F19 Public Gaming Center Discovery

Frontend repository: `sajadkhavas/turnoment`.

Frontend route: `/centers`.

Frontend F19 START_SHA:

`41bdbb90f127474ecabd61cb5ceda5db1b91ae49`

Frontend tracking Issue:

`sajadkhavas/turnoment#92`

Backend tracking Issue:

`#35`

Backend docs branch:

`docs/f19-public-gaming-center-discovery-contract`

Contract source:

`docs/F19_PUBLIC_GAMING_CENTER_DISCOVERY_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Planned endpoint:

`GET /api/v1/centers/`

Optional query surface:
- `city=<stable-city-slug>`;
- `page=<positive-integer>`.

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, settings/dependencies and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 4. Permanent F19 center-directory ownership truth

Backend/repository owns:
- public/published center membership and ordering;
- stable `centerId`;
- public navigation key projection (`publicId`) without pre-deciding the later canonical detail slug policy;
- center name;
- verification state;
- stable city identity/slug and district;
- public center summary;
- equipment/facility labels;
- optional cover image URL;
- nullable authoritative upcoming-tournament count;
- city facets/counts;
- city filtering;
- pagination.

Frontend may own:
- validated/shareable `city` and `page` URL state;
- final static Persian page copy/information hierarchy;
- presentation/formatting;
- accessibility/responsive behavior;
- canonical/robots metadata;
- deterministic fixture repository only for dev/test/visual QA.

Frontend MUST NOT derive production center membership, verification, equipment truth, city facets, filtering, pagination or tournament counts from local arrays.

## 5. F19 public list contract

Planned anonymous-safe read-only endpoint:

`GET /api/v1/centers/`

Response envelope:
- `schemaVersion = 1`;
- `filters.cities[]`;
- `activeQuery`;
- `items[]`;
- `pagination`.

Each city facet:
- stable `cityId`;
- stable city `slug`;
- public city `name`;
- non-negative authoritative `count`.

Each public center item:
- stable `centerId`;
- `publicId` navigation projection;
- `publicationState = published`;
- `name`;
- `verified`;
- stable city identity + district;
- public `summary`;
- `equipmentLabels[]`;
- `coverImage` nullable;
- `upcomingTournamentCount` nullable/non-negative.

Pagination integrity:
- positive `currentPage` and `pageSize`;
- non-negative `totalItems`;
- `totalPages = max(1, ceil(totalItems / pageSize))`;
- `currentPage <= totalPages`;
- returned item count does not exceed `pageSize`.

Stable IDs, public IDs and city identities/slugs must be unique in their projection scopes.

## 6. Ratings/reviews and verification policy

F19 v1 deliberately contains no rating/review fields.

The current accepted backend roadmap has no implemented ratings domain with authoritative aggregation, abuse handling and publication semantics. Therefore local/fabricated review numbers MUST NOT become production center truth.

A future accepted ratings/reviews domain may version/evolve this contract.

`verified` is a public backend-owned state projection. Private verification evidence/documents are never part of this public list contract.

## 7. F19 privacy / permission / API rules

- endpoint is anonymous-safe and read-only;
- when implemented by its owning runtime phase, public access explicitly opts into `AllowAny` because global backend permission defaults remain authenticated;
- validation/filtering/pagination remain backend-authoritative even when frontend runtime-validates responses;
- public response exposes no private phone/email/account/profile/group/permission/moderation-evidence/payment/refund/settlement/secret data;
- empty directory/filter result is valid and must never trigger fabricated production fallback records;
- `upcomingTournamentCount = null` means authoritative count unavailable, while `0` means authoritative zero.

## 8. `/centers/$id` compatibility boundary

F19 listing projects a `publicId` only to keep current frontend navigation functional.

The next frontend route recertification `/centers/$id` separately owns the stable public canonical identifier/slug decision. F19 must not silently freeze an opaque-ID SEO policy for that later route.

If the detail route later adopts a canonical slug, backend identity/redirect evolution must be explicit and compatible.

## 9. Official-source decisions for F19 alignment

Reviewed before documentation mutation:
- Django REST framework Permissions documentation;
- Django REST framework Versioning documentation;
- repository `docs/ENGINEERING_RULES.md`;
- repository `docs/PHASE_REGISTRY.md`.

Applied decisions:
- public endpoint access intent must be explicit with `AllowAny` under Turnoment's authenticated global default;
- public API remains under the established `/api/v1/` contract family;
- backend remains authoritative for filtering and public domain state;
- docs alignment cannot start the future gaming-centers/resources runtime phase ahead of P02.

## 10. Accepted previous cross-repo documentation alignments

F14 Teams alignment:
- backend Issue #25 CLOSED / COMPLETED;
- PR #26 MERGED;
- no Teams runtime Python implementation added.

F15 Challenge Hub alignment:
- backend Issue #27 CLOSED / COMPLETED;
- PR #28 MERGED;
- accepted backend main `c72ec545782a25719009ae329d74ffd13259d020`;
- post-main gate `34584360023` PASS;
- no Challenge runtime Python implementation added.

F16 Public Home Discovery alignment:
- backend Issue #29 CLOSED / COMPLETED;
- PR #30 MERGED;
- accepted backend main `335211d711c197a440e086bc570b86f2c5cd65f8`;
- post-main Backend Quality Gate `34591528685` PASS on Python 3.12 / 3.14;
- no Home discovery runtime Python implementation added.

F17 Public Tournament Discovery alignment:
- backend Issue #31 CLOSED / COMPLETED;
- PR #32 MERGED;
- accepted backend main `a5644ae4b4e64908088f389e43155c268fe6e29d`;
- post-main Backend Quality Gate `34609435404` PASS on Python 3.12 / 3.14;
- no tournament-discovery runtime Python implementation added.

F18 Public Game Catalog alignment:
- backend Issue #33 CLOSED / COMPLETED;
- docs head `c3bc950c69881b812a35e5fb39cda37d1c2c3da7`;
- PR #34 MERGED;
- backend merge/main `b0fc9ed73dc57aed6a28453745386489aaef0ceb`;
- post-main Backend Quality Gate `34631189236` PASS on Python 3.12 / 3.14;
- no Games runtime Python/model/migration/serializer/view/URL/dependency/phase-registry implementation was added.

Frontend freezes and contract alignments do not change backend runtime phase order.

## 11. F19 phase boundary

F19 contract alignment does NOT add:
- Python code;
- models/migrations;
- serializers/views/URLs;
- gaming-center runtime logic;
- dependencies/settings;
- phase-registry changes.

P02 remains the next backend runtime phase. The future gaming-centers/resources phase owns actual `GET /api/v1/centers/` implementation only after the accepted phase sequence reaches it.

Until then F19 remains exactly:

`FRONTEND MOCK / BACKEND PENDING`.

## 12. Exact F19 backend alignment NEXT

1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F19_PUBLIC_GAMING_CENTER_DISCOVERY_CONTRACT.md` from backend START `b0fc9ed73dc57aed6a28453745386489aaef0ceb`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #35;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend `main` lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend `main`;
10. record terminal docs-alignment evidence in Issue #35 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`.

Frontend F19 independently completes its implementation/SEO/QA/closeout chain. Completion of backend Issue #35 means contract documentation is aligned only; it MUST NOT be described as live gaming-center backend implementation.
