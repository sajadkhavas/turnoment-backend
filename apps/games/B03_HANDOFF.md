# B03 — Games / Rules / Public Discovery implementation handoff

Owning branch: `phase/b03-games-rules-discovery`
Starting revision after safe fast-forward: `0f5d44646b608106ad20db97ec8c559fa084e6ce`
Frozen frontend: `sajadkhavas/turnoment@1668109bae5ec7abb5e022e5857ffa65cc131501`
Issue: https://github.com/sajadkhavas/turnoment-backend/issues/49

## Intentional authority boundary

- `Game` holds database-authoritative public identity, canonical immutable slug, publication state, descriptions, platform labels, SEO and ordering. No mock games are copied into production tables.
- `CompetitiveFormat` is a game-owned format policy with a per-game unique key and team-size check constraint.
- `Ruleset` stores reviewed, revisioned policy documents, optionally game-scoped. At most one published revision exists for a policy key. Drafts and rules linked to unpublished games cannot be read anonymously.
- `Game` PK is a stable non-display identifier; no relationship is keyed on a display label. Foreign domains should reference `games.Game` by its PK, not its slug/name.
- Public list and detail exclude unpublished records. ORM `save()` triggers `full_clean()`; explicit DB constraints/indexes protect concurrent writers.
- Query `q` uses PostgreSQL `simple` full-text search (GIN expression index) plus compatible name substring search; `platform`, `slug`, and `gameId` are optional, strictly validated filters.
- All public views explicitly declare `AllowAny`, do not implement mutation methods, and retain P01 SessionAuthentication + CSRF defaults for the rest of the system.
- Catalogue v1 is non-paginated and limited to 100, as required by the frozen frontend parser; overflow fails closed with HTTP 503.

## Public endpoints

- `GET /api/v1/games/` — frozen F18 catalog response; `tournamentCount=null` until B05 supplies authoritative counts.
- `GET /api/v1/games/{slug}/` — frozen game detail response, game formats and pure related-data projection seam.
- `GET /api/v1/discovery/home/` — game-owned finder identities and date navigation hints. Cross-domain slots are deliberately empty, no fake tournament/center/ranking/financial claims.
- `GET /api/v1/rulesets/` — published ruleset summaries.
- `GET /api/v1/rulesets/{key}/` — published revision/sections.

## B99 integration seams / known dependency

- `apps.games.selectors.catalog_item` returns `tournamentCount=null` rather than counterfeit 0; B05 must provide authoritative counts after its tables are available.
- `apps.games.selectors.detail_projection(game, related=...)` accepts authoritative B04 (centers), B05 (tournaments), B09 (ranking) data matching the F02 shapes. Its default empty related-data placeholders are truthful only before those domains hold records. **B99 must connect a resolver before declaring full-stack API readiness.** No cross-domain models were fabricated here.
- `apps.games.selectors.home_game_projection` currently returns game-owned finder data only; B99 composes its other slots from B04/B05/B09. `popularGames` is intentionally empty until authoritative active tournament counts can be provided.
- `Ruleset` is a database-ready policy publication model; existing frozen frontend `/rules` remains backed by reviewed version-controlled content at its exact SHA. This branch does not silently replace it or copy frontend fixtures as authority. A future adapter decision is integration-owned.
- Admin permissions for writing catalog and rules are Django platform-admin only; no venue membership or staff object edit API is created.
- No financial execution, refund command or payout workflow is added; policy text is informational only.
- Shared wiring intentionally changed only `config/settings/base.py` (two installed apps) and `config/urls.py` (two URL includes). Other workstreams must reconcile those files during integration.

## Upstream design sources

- https://docs.djangoproject.com/en/6.0/ref/models/constraints/ — model-level uniqueness/check constraints supplement validation
- https://docs.djangoproject.com/en/6.0/ref/contrib/postgres/search/ — PostgreSQL search with GIN indexing
- https://docs.djangoproject.com/en/6.0/topics/migrations/ — versioned, deterministic schema migrations
- https://www.django-rest-framework.org/api-guide/permissions/ — public views explicitly opt into AllowAny under the authenticated default
- https://www.django-rest-framework.org/api-guide/serializers/ — backend validation and projection shape
- https://docs.djangoproject.com/en/6.0/topics/db/transactions/ — transactions for later mutating command services

FINANCIAL EXECUTION ADDED: NO
