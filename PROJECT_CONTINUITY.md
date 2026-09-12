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
9. keep docs-only alignment work out of Python/models/migrations/serializers/views/URLs/settings/dependencies/workflows/phase-registry;
10. keep runtime phase order authoritative even when frontend architecture is frozen first.

## 2. Current backend truth

Repository: `sajadkhavas/turnoment-backend`

Current live backend `main` / F22 documentation-alignment START_SHA:

`44f18e462f63c625bc02e07ef93c15f1c385dcd0`

P00 and P01 remain terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry orders runtime work through games/catalog, gaming centers/resources, tournaments/registrations, rankings, then later competitive slices. Cross-repo documentation alignment MUST NOT reorder that sequence.

Current runtime truth remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

## 3. Accepted documentation alignments

F19 Public Gaming Center Discovery is terminal: Issue #35 CLOSED / COMPLETED; PR #36 MERGED; backend main `b6421e1e76e846c89d799fe4860bc11c8242f2f8`; PR-context Backend Quality Gate `34641469931` and post-main `34641761119` PASS on Python 3.12 / 3.14.

F20 Public Gaming Center Detail is terminal: Issue #37 CLOSED / COMPLETED; PR #38 MERGED; backend main `e8e48061cba201b3a12ac534ef97f22565bea5a3`; PR-context gate `34653701760` and post-main `34653883656` PASS on Python 3.12 / 3.14.

F21 Public Player Ranking is terminal documentation alignment: Issue #39 CLOSED / COMPLETED; PR #40 MERGED; backend main `44f18e462f63c625bc02e07ef93c15f1c385dcd0`; PR-context Backend Quality Gate `34658090539` and post-main `34658179049` PASS on Python 3.12 / 3.14.

None of these alignments added owning runtime-domain implementation or reordered backend phases.

## 4. Active cross-repo alignment — F22 Public Player Profile

Frontend repository: `sajadkhavas/turnoment`.

Frontend route:

`/players/$username`

Frontend F22 START_SHA:

`36e8685192fede45da8c4e82c32bdc41a2db1be2`

Frontend source checkpoint used for this alignment:

`d8e2cb8448837b3d63cb9727ae44b1a892ab7d64`

Frontend tracking Issue:

`sajadkhavas/turnoment#101`

Backend tracking Issue:

`#41`

Backend docs branch:

`docs/f22-public-player-profile-contract`

Contract source:

`docs/F22_PUBLIC_PLAYER_PROFILE_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Frontend-reserved target endpoint:

`GET /api/v1/players/{username}/public-profile/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. Existing P01 public-player runtime truth

P01 already exposes a public player endpoint, but it is not the F22 contract:

`GET /api/v1/players/<gamer_tag>/`

Current implementation facts:
- route lookup parameter is `gamer_tag`;
- lookup is case-insensitive `PlayerProfile.gamer_tag`;
- `PlayerProfile` currently has no stable public `username` field;
- gamer tag is mutable display/profile identity under the current P01 model, not the new F22 navigation identity;
- current `PublicPlayerSerializer` exposes `id`, `gamer_tag`, `display_name`, free-text `city`, `bio`, and `avatar_key` only;
- current endpoint explicitly uses `AllowAny` and returns public 404 when no active matching profile exists.

F22 documentation MUST NOT silently reinterpret this existing gamer-tag route as stable username lookup. Runtime compatibility/migration belongs to an accepted future runtime phase.

## 6. F22 target identity / publication boundary

F22 target semantics:
- `playerId` = stable backend relation identity;
- `username` = stable public profile-navigation identity;
- `gamerTag` = public display text only and never a relation key;
- public profile must be explicitly published before projection;
- public search visibility is projected as `indexable | noindex`;
- private, unpublished, invalid and nonexistent public lookups collapse to the same not-found surface so the public API does not expose account existence through distinct outcomes.

Before F22 can be integrated live, an owning runtime phase must establish stable `username` storage/uniqueness/normalization and an explicit compatibility strategy for the existing gamer-tag endpoint. The old endpoint must not have its lookup meaning changed silently.

## 7. F22 target projection / ownership

Planned strict v1 response contains only public-safe data:
- `schemaVersion=1`;
- `publicationState=published`;
- `searchVisibility=indexable|noindex`;
- stable `playerId`, stable `username`, public `gamerTag`;
- optional public avatar, stable city projection and public bio;
- bounded competitive snapshots keyed by stable game/season/rating-type identity;
- authoritative rating/rank/record/movement;
- bounded recent finalized public result projection.

Backend owns publication, identity, competitive membership, rating/rank/record/movement/result truth and all cross-domain relations. Frontend owns presentation, SEO/canonical/robots, accessibility/responsive behavior and deterministic dev/test fixtures only.

Frontend MUST NOT calculate authoritative win rate, rating, rank, movement, result validity or eligibility.

## 8. Privacy / permission rules

Future F22 endpoint must explicitly opt into `AllowAny` under Turnoment's authenticated global default and return only the accepted public projection.

Forbidden public data includes phone, email, real/private display identity unless separately accepted as public, `interview_opt_in`, auth/session/OTP data, groups/permissions, moderation evidence, verification documents, payment/refund/settlement data, secrets and private account/profile fields.

Frontend runtime validation never replaces backend publication/privacy/domain validation.

## 9. Official DRF decisions reviewed for F22

Current official Django REST framework guidance reviewed before documentation mutation:
- Permissions: https://www.django-rest-framework.org/api-guide/permissions/ — `AllowAny` explicitly communicates unrestricted public access and per-view policy overrides the global default.
- Generic views: https://www.django-rest-framework.org/api-guide/generic-views/ — detail projections use explicit lookup/queryset behavior; the implementation phase may choose APIView or a generic detail view but must preserve publication/privacy semantics.
- Serializers: https://www.django-rest-framework.org/api-guide/serializers/ — the external representation and lookup fields must match the accepted API contract.
- Validators: https://www.django-rest-framework.org/api-guide/validators/ — validation belongs explicitly at the serializer/API boundary as well as in database/domain constraints where applicable.
- Exceptions: https://www.django-rest-framework.org/api-guide/exceptions/ — not-found resources map to HTTP 404; F22 intentionally uses a common public not-found outcome for absent/non-public identities.

These references do not authorize runtime implementation in this docs-only alignment.

## 10. F22 documentation-alignment acceptance chain

Required chain:
1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F22_PUBLIC_PLAYER_PROFILE_CONTRACT.md` from backend START `44f18e462f63c625bc02e07ef93c15f1c385dcd0`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #41;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend-main lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend main;
10. record terminal documentation-alignment evidence in Issue #41 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`;
12. keep runtime truth `FRONTEND MOCK / BACKEND PENDING` until owning runtime phases actually ship.
