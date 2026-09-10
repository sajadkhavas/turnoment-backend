# F13 — Player Achievements Hub Contract

Status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT`

Frontend workstream: `sajadkhavas/turnoment#68`

Frontend route: `/dashboard/achievements`

Backend START_SHA: `e81b13a0de6936ded0879d4310eab3883a7556a6`

Runtime truth: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains `P02 — Games / Catalog Foundation`.

## 1. Scope

This document reserves the production contract needed by the final private F13 Achievements Hub. It does not start or reorder a backend runtime phase and does not claim that an achievements Django domain exists yet.

Planned authenticated endpoint:

`GET /api/v1/me/achievements/`

F13 is read-only. No achievement claim/award mutation endpoint is introduced.

## 2. Authentication / authorization

- Django Session Authentication is the web authentication truth.
- Browser requests use `credentials: include`.
- The endpoint is private and server-authorized for the current player.
- Frontend route access checks are UX/navigation boundaries only.
- No localStorage/sessionStorage bearer token is introduced.

## 3. Query contract

Optional query parameters:

- `status=locked|in-progress|unlocked`; absence means all statuses.
- `category=<stable-category-id>`; relational filtering uses the server-issued category ID, never display text.
- `sort=default|recent|progress`; absence means the server-defined default ordering.
- `page=<positive-integer>`; absence means page 1.

Frontend validation is convenience/navigation validation only. Backend validation remains authoritative.

Ordering semantics are backend-owned. `recent` prioritizes server-defined achievement activity/unlock recency and `progress` prioritizes server-defined progress ordering; the frontend MUST NOT locally reorder the returned projection.

## 4. Response projection

```text
player
  playerId
  gamerTag

timezone                         # IANA timezone for unlockedAt presentation

summary
  total
  unlocked
  inProgress
  locked

categories[]
  categoryId
  name

items[]
  achievementId
  code
  title
  description
  category
    categoryId
    name
  status                         # locked | in-progress | unlocked
  progress?                      # nullable
    current                      # non-negative integer
    target                       # positive integer
    percent                      # integer 0..100, server-authoritative
  unlockedAt?                    # offset-aware ISO datetime; unlocked only

pagination
  currentPage
  totalPages
  totalItems
```

All display strings are product content supplied by the authoritative projection. Stable IDs/codes are relational identity; titles/descriptions are never used as keys.

## 5. Authoritative integrity

Server/repository owns:

- which achievement definitions exist;
- stable `achievementId` and `code`;
- category identity/membership and available category filters;
- current-player achievement status;
- whether progress exists for an achievement;
- progress `current`, `target` and `percent` when present;
- `unlockedAt` timestamp;
- summary counts;
- filtering, ordering and pagination.

Required integrity expectations:

- `summary.unlocked + summary.inProgress + summary.locked == summary.total`;
- `pagination.currentPage <= pagination.totalPages` and `pagination.totalPages >= 1`;
- filtered `pagination.totalItems <= summary.total`;
- returned item/category IDs are stable non-empty identifiers;
- an item category must correspond to one server-provided category option;
- achievement IDs and achievement codes are unique within a response page;
- `progress.target > 0`, `progress.current >= 0`, `progress.percent` is `0..100`;
- `in-progress` requires progress and cannot expose `unlockedAt`;
- `locked` cannot expose `unlockedAt`;
- `unlocked` requires `unlockedAt`;
- when an unlocked item exposes progress, `percent=100` and `current >= target`;
- when an in-progress item exposes progress, `0 < current < target` and `0 < percent < 100`;
- backend may omit progress for binary locked/unlocked achievements;
- server percentage is authoritative and the frontend does not infer status from percentage.

The owning future backend phase may refine storage/event mechanics while preserving these external meanings or versioning the contract explicitly.

## 6. Frontend ownership

Frontend may own only presentation/navigation concerns:

- validated URL state;
- Persian labels and explanatory UI copy around server content;
- formatting `unlockedAt` using the supplied timezone;
- visual progress bars using the authoritative percentage;
- responsive layout, keyboard interaction and accessible status/progress semantics;
- deterministic fixture adapter for development/test/visual QA behind the same repository interface.

Frontend MUST NOT:

- infer or award an achievement from local Match/Tournament/Challenge history;
- convert progress into an unlock decision;
- invent XP, points, coins, money, prizes or claim flows;
- invent trophy grades, rarity or global population percentages;
- infer Challenge eligibility/rating state;
- create social comparison/friend behavior;
- invent an Achievement Detail route/link;
- mutate `/dashboard/challenges` as part of F13.

## 7. Product boundary

F13 is a platform achievements view, not a copy of PlayStation/Steam trophy economies. External achievement systems may inform information hierarchy only. Turnoment achievement definitions and conditions remain server-defined product data.

No requirement in this contract implies that achievements are based only on wins, match count, tournament count, challenges or any other particular metric. Those definitions belong to future authoritative product/domain configuration.

## 8. Runtime / phase boundary

This alignment changes documentation only. It MUST NOT modify:

- Python application code;
- models or migrations;
- serializers, views or URLs;
- dependencies;
- `docs/PHASE_REGISTRY.md`;
- backend phase ordering.

Until an owning backend runtime phase implements, permission-tests and merges this endpoint, runtime remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`.
