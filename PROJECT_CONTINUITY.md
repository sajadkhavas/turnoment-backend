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

Current live backend `main` / F21 documentation-alignment START_SHA:

`e8e48061cba201b3a12ac534ef97f22565bea5a3`

P00 and P01 remain terminally frozen.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

The backend phase registry orders runtime work through games/catalog, gaming centers/resources, tournaments/registrations, rankings, then later competitive slices. Cross-repo documentation alignment MUST NOT reorder that sequence.

Current runtime truth remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

## 3. Accepted public gaming-center alignments

F19 Public Gaming Center Discovery documentation alignment is terminal:
- backend Issue #35 — CLOSED / COMPLETED;
- PR #36 — MERGED;
- backend merge/main `b6421e1e76e846c89d799fe4860bc11c8242f2f8`;
- PR-context Backend Quality Gate `34641469931` — PASS on Python 3.12 / 3.14;
- post-main Backend Quality Gate `34641761119` — PASS on Python 3.12 / 3.14.

F20 Public Gaming Center Detail documentation alignment is terminal:
- backend Issue #37 — CLOSED / COMPLETED;
- PR #38 — MERGED;
- backend merge/main `e8e48061cba201b3a12ac534ef97f22565bea5a3`;
- PR-context Backend Quality Gate `34653701760` — PASS on Python 3.12 / 3.14;
- post-main Backend Quality Gate `34653883656` — PASS on Python 3.12 / 3.14.

Neither alignment added gaming-center runtime Python/models/migrations/serializers/views/URLs/settings/dependencies or reordered backend phases.

## 4. Active cross-repo alignment — F21 Public Player Ranking

Frontend repository: `sajadkhavas/turnoment`.

Frontend route:

`/ranking`

Frontend F21 START_SHA:

`b585e1e421c2e0febedf53e43349a23666004338`

Frontend tracking Issue:

`sajadkhavas/turnoment#98`

Frontend source checkpoint used for this alignment:

`2d75596a31440dcd795ea609926a02e7a478e71e`

Backend tracking Issue:

`#39`

Backend docs branch:

`docs/f21-public-player-ranking-contract`

Contract source:

`docs/F21_PUBLIC_PLAYER_RANKING_CONTRACT.md`

Status:

`IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Planned endpoint:

`GET /api/v1/rankings/`

This alignment is documentation-only. Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows and `docs/PHASE_REGISTRY.md` are forbidden from changing here.

## 5. F21 permanent ownership boundary

Future backend/repository authority includes:
- leaderboard membership/order/rank;
- stable `playerId`;
- public profile `username`;
- gamer tag projection;
- stable game/city identity;
- Tournament Rating and Challenge Rating truth;
- active ranking-type rating projection;
- match-record projection;
- rank movement;
- game/season/region/type facet membership/normalization;
- filtering and pagination.

Frontend owns only validated/shareable navigation state, presentation, SEO/canonical/robots, accessibility/responsive behavior and deterministic dev/test fixtures.

Frontend MUST NOT calculate official rank, rating, movement or challenge eligibility.

## 6. F21 query and response contract

Planned query dimensions:
- `game=<stable-game-slug>`;
- `season=<stable-season-slug>`;
- `region=<stable-region-slug>`;
- `type=tournament|challenge`;
- `page=<positive-integer>`.

Planned strict v1 response includes:
- `schemaVersion=1`;
- backend-projected game/season/region/ranking-type facets;
- authoritative normalized `activeQuery`;
- ranking rows with stable player/public-profile/game/city identities;
- authoritative `rank`, one `rating` paired with `ratingType`, played/wins/losses/draws and rank movement;
- page-number pagination metadata.

Tournament Rating and Challenge Rating remain separate truths. F21 listing does not calculate challenge eligibility in the browser and does not require eligibility in the v1 public ranking row.

## 7. Public privacy / integrity rules

The future endpoint may project only public-safe ranking identity/statistics. It must exclude private account/contact/auth/moderation/verification/payment/secret data.

Identity rules:
- `playerId` = stable backend relation identity;
- `username` = public profile-navigation identity;
- gamer tag = display text, never a relation key.

Integrity rules include:
- deterministic authoritative order before pagination;
- rows match active game and rating type;
- page identities/ranks are unique;
- match-record arithmetic is internally consistent;
- movement semantics are explicit;
- frontend syntax validation never replaces backend domain validation.

## 8. Permissions / DRF decisions

Current official DRF guidance was reviewed before F21 documentation mutation:
- Permissions: future public read endpoint explicitly opts into `AllowAny` under Turnoment's authenticated global default;
- Filtering: game/season/region/type restrictions are server-side authoritative;
- Pagination: `PageNumberPagination` is compatible with the public `page` query, with deterministic ordering required before pagination.

No arbitrary client ordering is accepted in F21 v1.

## 9. F21 documentation-alignment acceptance chain

Required chain:
1. commit exactly `PROJECT_CONTINUITY.md` and `docs/F21_PUBLIC_PLAYER_RANKING_CONTRACT.md` from backend START `e8e48061cba201b3a12ac534ef97f22565bea5a3`;
2. verify ahead 1 / behind 0 / exactly one commit / exactly two Markdown files;
3. require Backend Quality Gate PASS on Python 3.12 and 3.14;
4. open docs PR without auto-closing Issue #39;
5. require PR-context Backend Quality Gate PASS;
6. require mergeable=true, unresolved review threads=0 and exact pre-merge backend main lock;
7. merge with expected-head lock;
8. require post-main Backend Quality Gate PASS;
9. reverify exact live backend main;
10. record terminal documentation-alignment evidence in Issue #39 and close completed;
11. keep Backend NEXT exactly `P02 — Games / Catalog Foundation`;
12. continue to describe runtime truth as `FRONTEND MOCK / BACKEND PENDING` until the owning runtime phase actually ships.
