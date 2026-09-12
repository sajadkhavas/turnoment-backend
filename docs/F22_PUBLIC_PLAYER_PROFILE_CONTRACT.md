# F22 — Public Player Profile Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/players/$username`

Frontend tracking Issue: `sajadkhavas/turnoment#101`

Backend tracking Issue: `#41`

Backend START_SHA:

`44f18e462f63c625bc02e07ef93c15f1c385dcd0`

Frontend F22 START_SHA:

`36e8685192fede45da8c4e82c32bdc41a2db1be2`

Frontend exact source checkpoint used for this alignment:

`d8e2cb8448837b3d63cb9727ae44b1a892ab7d64`

## 1. Scope and phase-order law

This file aligns the future backend public-player-profile contract with frontend F22. It does **not** implement player-profile, games, seasons, rankings, tournaments or results runtime code and does not reorder backend phases.

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`

Runtime remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

The F22 frontend may be frozen against this planned contract before backend integration, but it must not be described as live until the owning backend phases implement, permission-test and merge the required runtime behavior.

## 2. Existing P01 endpoint is not the F22 endpoint

P01 already exposes:

`GET /api/v1/players/<gamer_tag>/`

Current runtime behavior at backend START:
- URL lookup parameter is `gamer_tag`;
- `PublicPlayerView` queries `PlayerProfile.gamer_tag__iexact` and requires the related user to be active;
- no stable public `username` field exists in `User` or `PlayerProfile`;
- `gamer_tag` is currently a case-insensitively unique profile field and may be changed through the private profile API;
- `PublicPlayerSerializer` returns identity/profile-only data: user UUID as `id`, `gamer_tag`, `display_name`, free-text `city`, `bio`, and `avatar_key`;
- current public endpoint explicitly uses `AllowAny` and returns 404 when no active matching profile exists.

F22 MUST NOT silently rename or reinterpret this existing lookup as a stable username. Doing so would change public URL identity semantics without a migration/compatibility contract.

## 3. Target F22 endpoint

Frontend F22 reserves the following future endpoint:

`GET /api/v1/players/{username}/public-profile/`

The endpoint is read-only and anonymous-safe for an explicitly published public projection only.

Required request identity:
- `username` is normalized/stable public navigation identity;
- the response `username` must exactly identify the requested public profile under the accepted normalization policy;
- display `gamerTag` is not a lookup relation key.

Before this endpoint can become live, an accepted runtime phase must establish stable username storage, uniqueness, normalization and lifecycle semantics.

## 4. Username / gamer-tag migration law

Target identity meanings are distinct:
- `playerId` = stable backend relation identity;
- `username` = stable public navigation identity for `/players/{username}`;
- `gamerTag` = public display text only.

A future runtime implementation must explicitly decide and test migration/compatibility from the current gamer-tag endpoint. Acceptable implementation work may include a versioned compatibility alias or another explicit migration strategy, but it must satisfy all of the following:
- no ambiguous collision between username and gamer-tag identities;
- no silent change of the old endpoint's lookup meaning;
- no display-name relation joins;
- no public URL that can resolve to a different player solely because a gamer tag changed;
- compatibility/deprecation behavior is tested and documented before activation.

This documentation alignment does not choose or implement a database migration. It freezes the semantic boundary that the owning runtime phase must satisfy.

## 5. Public publication / existence-leak policy

The F22 target endpoint returns the full projection only when the profile is eligible for public publication.

Public lookup outcomes intentionally collapse:
- nonexistent identity;
- unpublished/private profile;
- account/profile not eligible for public projection;
- syntactically/semantically invalid public identity after accepted validation.

These states must not expose distinct account-existence clues to anonymous consumers. The public API returns the same not-found style outcome for identities that are not publicly projectable.

The frontend maps HTTP 404 to its single public not-found state and must not infer whether an account exists behind that outcome.

## 6. Planned strict v1 response projection

```text
schemaVersion: 1
publicationState: published
searchVisibility: indexable | noindex
playerId
username
gamerTag
avatarUrl: string | null
city: object | null
  cityId
  slug
  name
publicBio: string | null
competitiveSnapshots[]
  snapshotId
  game
    gameId
    slug
    name
  season
    seasonId
    slug
    label
  ratingType: tournament | challenge
  rating
  rank: positive integer | null
  played
  wins
  losses
  draws
  movement: object | null
    direction: up | down | flat
    positions
recentResults[]
  resultId
  tournament
    tournamentId
    name
  game
    gameId
    slug
    name
  outcome: win | loss | draw
  opponentGamerTag: string | null
  completedAt
```

`completedAt` is an offset-aware ISO datetime.

`avatarUrl`, city and public bio are nullable because absence is a legitimate public state and the API must not fabricate substitutes.

## 7. Projection integrity rules

Target response invariants:
- `schemaVersion` is exactly `1`;
- `publicationState` is exactly `published` for successful responses;
- `searchVisibility` is backend-projected `indexable` or `noindex` and is not inferred from profile completeness by the browser;
- player, game, season, tournament, snapshot and result relations use stable identities rather than display labels;
- competitive snapshot IDs are unique;
- `(gameId, seasonId, ratingType)` snapshot scope is unique within one profile response;
- recent result IDs are unique;
- wins + losses + draws equals played for each projected competitive snapshot;
- flat movement has zero positions;
- up/down movement has a positive position count;
- rank is positive when present;
- rating/record/movement/result truth is backend-authoritative and must not be reconstructed in the frontend;
- returned public username must match the resolved requested identity under the accepted normalization policy.

The owning runtime phases may enforce stronger database/domain constraints when the underlying models exist.

## 8. Competitive-domain ownership

F22 crosses several future backend domains. Documentation alignment does not collapse those phases into accounts/P01.

Backend authority eventually includes:
- published player identity and search visibility;
- stable city identity where publicly projected;
- public game/season identities;
- Tournament Rating and Challenge Rating truth;
- rank and rank movement;
- match record;
- finalized public tournament/result membership;
- recent result validity/order;
- all publication and relation integrity.

Frontend owns:
- route presentation and interaction;
- title/meta/canonical/robots based on the authoritative projection;
- accessibility/responsive behavior;
- natural public copy;
- deterministic fixtures for development/test/visual QA behind the same typed repository interface.

Frontend MUST NOT calculate authoritative win rate, rating, rank, movement, result validity or challenge eligibility.

## 9. Privacy boundary

F22 public response may contain only explicitly accepted public-safe fields.

Forbidden fields/data include:
- phone;
- email;
- private/legal/real name unless a future separately accepted public identity policy explicitly authorizes it;
- `interview_opt_in`;
- authentication/session/OTP state;
- staff/groups/permissions;
- moderation/dispute evidence not explicitly public;
- verification documents/evidence;
- payment/refund/settlement data;
- internal flags/secrets/configuration;
- private profile/account fields not listed in the accepted public projection.

The current P01 private serializer may continue to own private fields; their existence is not permission to expose them from F22.

## 10. Permission and request rules

Turnoment's global API policy remains authenticated. The future F22 read endpoint must explicitly declare:

`AllowAny`

for anonymous public access, matching the project's engineering rule that public endpoints opt in explicitly.

Expected HTTP behavior:
- GET only for the F22 public projection;
- 200 only for a valid published public projection;
- 404-style public outcome for absent/non-public identities;
- other server/integration failures remain failures and must not fall back to fixture/demo data in production.

Frontend `credentials: include` is compatible with same-origin session behavior but does not convert a public read into an authenticated-only endpoint and does not authorize extra fields.

## 11. Validation boundary

Frontend syntax/runtime validation is defense in depth only.

Backend implementation must validate:
- username syntax/normalization and resolution;
- publication eligibility;
- serializer/output field constraints;
- game/season/rating/result relation validity;
- uniqueness/integrity invariants required by the projection;
- visibility of every optional/public field.

Serializer validation and database/domain constraints should be used where each is authoritative. Unknown/private fields must not leak into the public representation.

## 12. Search visibility relationship

Backend owns only the public `searchVisibility` product truth for the profile projection. Frontend owns emitted search metadata:
- `indexable` → route may emit `index,follow` with its canonical public profile URL;
- `noindex` → route emits `noindex,follow` while remaining publicly viewable;
- public not-found → frontend emits `noindex,nofollow`.

Backend does not author HTML SEO metadata, and frontend must not override a backend `noindex` profile into indexable state.

## 13. Official DRF documentation decisions

Reviewed before this docs-only alignment:

- Permissions — https://www.django-rest-framework.org/api-guide/permissions/
  - permissions are evaluated before view execution;
  - `AllowAny` explicitly documents unrestricted public access and can override the authenticated global default at the view level.
- Generic views — https://www.django-rest-framework.org/api-guide/generic-views/
  - detail views require deliberate queryset/lookup behavior; a future implementation must resolve the stable public username with publication filtering rather than display-name lookup.
- Serializers — https://www.django-rest-framework.org/api-guide/serializers/
  - external API representation is serializer-owned and lookup fields may be explicitly configured when URL identity differs from primary key.
- Validators — https://www.django-rest-framework.org/api-guide/validators/
  - serializer validation is explicit and reusable; it does not replace database/domain invariants where those apply.
- Exceptions — https://www.django-rest-framework.org/api-guide/exceptions/
  - resource-not-found behavior maps to HTTP 404; F22 deliberately normalizes non-public/absent public identities to one public not-found outcome.

Applied decisions:
- future F22 endpoint explicitly uses `AllowAny`;
- stable username lookup is explicit and distinct from gamer-tag display identity;
- public serializer is a narrow allow-list projection;
- publication filtering occurs before public serialization;
- this alignment does not change P01 runtime or start later competitive domains.

## 14. Current P01 compatibility boundary

Current P01 runtime remains valid and unchanged by this document:

`GET /api/v1/players/<gamer_tag>/`

It is an identity/profile projection, not the final F22 competitive profile endpoint. Until the future username/publication/competitive runtime work is accepted:
- existing clients may continue to use P01 semantics;
- F22 production adapter must not be described as integrated;
- no documentation statement may claim `/api/v1/players/{username}/public-profile/` exists in current backend runtime;
- runtime truth remains `FRONTEND MOCK / BACKEND PENDING`.

## 15. Documentation-alignment acceptance

This alignment may change exactly two Markdown files:
1. `PROJECT_CONTINUITY.md`;
2. `docs/F22_PUBLIC_PLAYER_PROFILE_CONTRACT.md`.

It must not change Python, models, migrations, serializers, views, URLs, settings, dependencies, workflows or `docs/PHASE_REGISTRY.md`.

Required evidence before closing backend Issue #41:
- one docs commit / two Markdown files / ahead 1 / behind 0;
- Backend Quality Gate PASS on Python 3.12 and 3.14;
- docs PR-context gate PASS;
- mergeable=true;
- unresolved review threads=0;
- exact pre-merge backend-main lock;
- expected-head merge;
- post-main Backend Quality Gate PASS;
- exact live backend-main verification;
- terminal evidence in Issue #41 and close `completed`;
- Backend NEXT still exactly `P02 — Games / Catalog Foundation`.
