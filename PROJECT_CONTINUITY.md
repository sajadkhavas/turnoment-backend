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

## 2. Repository truth

Repository: `sajadkhavas/turnoment-backend`

Current accepted backend main / F18 docs-alignment START_SHA:

`a5644ae4b4e64908088f389e43155c268fe6e29d`

P00 and P01 are terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Cross-repo frontend contracts may be documented ahead of runtime implementation, but they do not start/reorder backend phases and MUST remain represented as:

`FRONTEND MOCK / BACKEND PENDING`

until the owning backend domain is implemented, permission-tested and merged under the phase protocol.

## 3. Accepted cross-repo documentation alignments

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
- post-main gate `34591528685` PASS on Python 3.12 / 3.14;
- no Home discovery runtime Python implementation added.

F17 Public Tournament Discovery alignment:
- backend Issue #31 CLOSED / COMPLETED;
- docs head `1566574c26a747edee785fcc2ff76f014fc63b3e`;
- PR #32 MERGED;
- accepted backend main `a5644ae4b4e64908088f389e43155c268fe6e29d`;
- post-main gate `34609435404` PASS on Python 3.12 / 3.14;
- no tournament-discovery runtime Python implementation added.

Frontend freezes do not change backend runtime phase order.

## 4. Active cross-repo alignment — F18 Public Game Catalog

Frontend repository: `sajadkhavas/turnoment`.

Frontend route: `/games`.

Frontend F18 START_SHA:

`73955783add94c562f4eea0bb55300aab077c342`

Frontend tracking Issue: `sajadkhavas/turnoment#89`.

Backend tracking Issue: `#33`.

Backend docs branch:

`docs/f18-public-game-catalog-contract`

Contract source:

`docs/F18_PUBLIC_GAME_CATALOG_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ONLY`

Planned endpoint already reserved in the frontend↔backend baseline:

`GET /api/v1/games/`

This alignment refines the response/ownership contract so F18 `/games` does not retain browser-owned catalog membership or tournament counts.

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, dependencies and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. Permanent F18 game-catalog ownership truth

Backend/repository owns:
- public/published catalog membership;
- catalog ordering;
- stable `gameId`;
- canonical public slug;
- authoritative game `name` and `shortName`;
- supported platform labels;
- game-entity catalog description;
- optional cover image URL;
- optional tournament-count projection only when authoritative.

Frontend may own:
- final static Persian page copy/information hierarchy;
- presentation/formatting;
- accessibility/responsive behavior;
- canonical/robots metadata;
- crawlable navigation to `/games/{slug}` and `/tournaments?game=<stable-game-id>`;
- deterministic fixture repository only for dev/test/visual QA.

Frontend MUST NOT derive production catalog membership, canonical identity or tournament counts from local tournament arrays.

## 6. F18 public list contract

Planned anonymous-safe read-only endpoint:

`GET /api/v1/games/`

Response page:
- `schemaVersion = 1`;
- `totalItems`;
- `items[]`.

Each published game item:
- `gameId` — stable relation/navigation key;
- `slug` — canonical public slug compatible with game detail;
- `publicationState = published`;
- `name`;
- `shortName`;
- `description`;
- `platforms[]`;
- `coverImage` nullable;
- `tournamentCount` nullable/non-negative and only supplied when backend-authoritative.

Required integrity:
- stable IDs unique in the page;
- canonical slugs unique in the page;
- no duplicate platform labels within one game;
- `totalItems` reflects the complete public list projection returned by this contract version;
- nullable count means the authoritative count is intentionally unavailable, not zero.

The list identity MUST remain compatible with the already-reserved detail contract:

`GET /api/v1/games/{slug}/`

## 7. Privacy / permission / API rules

- endpoint is anonymous-safe and read-only;
- when implemented, public access must explicitly opt into `AllowAny` because global backend permission defaults remain authenticated;
- validation remains backend-authoritative even when the frontend runtime-validates the response;
- public response exposes no phone/email/private account/profile/group/permission/moderation/payment/refund/settlement data;
- no popularity/search-volume/viewership/prize/ranking superlative may be fabricated as catalog truth;
- empty public catalog is a valid product state and must never trigger fabricated production fallback records.

## 8. Phase boundary

F18 contract alignment does NOT add:
- Python code;
- models/migrations;
- serializers/views/URLs;
- games/catalog runtime logic;
- dependencies;
- phase-registry changes.

P02 is still the next backend phase and is the owner of actual Games / Catalog runtime implementation. Until P02 implements and permission-tests the endpoint, F18 remains exactly:

`FRONTEND MOCK / BACKEND PENDING`.

## 9. Exact F18 backend alignment NEXT

1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F18_PUBLIC_GAME_CATALOG_CONTRACT.md` from backend START `a5644ae4b4e64908088f389e43155c268fe6e29d`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #33;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend `main` lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend `main`;
10. record terminal docs-alignment evidence in Issue #33 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`.

Frontend F18 independently completes its implementation/SEO/QA/closeout chain. Completion of backend Issue #33 is contract alignment only and MUST NOT be described as a live Games backend implementation.
