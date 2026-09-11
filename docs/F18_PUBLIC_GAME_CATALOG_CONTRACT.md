# F18 — Public Game Catalog Contract Alignment

Status: `IN PROGRESS — DOCUMENTATION ALIGNMENT ONLY`

Frontend route: `/games`

Frontend workstream: `F18 — Public Game Catalog`

Frontend tracking Issue: `sajadkhavas/turnoment#89`

Backend tracking Issue: `#33`

Backend START_SHA:

`a5644ae4b4e64908088f389e43155c268fe6e29d`

Runtime truth:

`FRONTEND MOCK / BACKEND PENDING`

Backend NEXT:

`P02 — Games / Catalog Foundation`

## 1. Purpose

Freeze the public game-list ownership/projection contract before P02 runtime implementation so the frontend `/games` route can have a stable production adapter without becoming authoritative for catalog membership, canonical identity or tournament counts.

This document does not implement an endpoint.

## 2. Planned endpoint

`GET /api/v1/games/`

Properties:
- read-only;
- anonymous-safe;
- when implemented under P02, explicitly opts into public `AllowAny` because backend global permission defaults remain authenticated;
- no session identity is required to read the public catalog;
- no private account/contact/permission/payment/moderation information may be emitted.

## 3. Response projection

```text
schemaVersion: 1
totalItems: non-negative integer
items[]
  gameId
  slug
  publicationState: published
  name
  shortName
  description
  platforms[]
  coverImage: string | null
  tournamentCount: non-negative integer | null
```

### Identity

`gameId` is the stable relation/navigation key used for API filtering and cross-domain relations.

`slug` is the canonical public route key and must be compatible with the reserved detail endpoint:

`GET /api/v1/games/{slug}/`

Display names are never relation keys.

### Membership / ordering

The backend owns which games are published and the order returned by the public catalog.

The frontend MUST NOT load a local full game array and treat it as authoritative production membership/order.

### Tournament count

`tournamentCount` is nullable.

If supplied as an integer, it is an authoritative backend projection according to the owning product definition. If the owning backend domain cannot provide that count authoritatively yet, return `null`; the frontend must display neutral copy rather than invent/derive the count from local tournament arrays.

`0` means an authoritative zero and is distinct from `null`.

## 4. Integrity requirements

- `schemaVersion` is exactly `1` for this contract generation;
- IDs are unique within the public page;
- canonical slugs are unique within the public page;
- platform labels are non-empty and unique per game;
- `tournamentCount`, when present, is non-negative;
- `totalItems` equals the complete item list returned by this non-paginated v1 projection;
- unpublished/private games are excluded from the public projection;
- empty catalog is valid and must return an empty list rather than fabricated records.

If P02 later requires pagination due to real catalog scale, that is a versioned/controlled contract evolution rather than silent frontend inference.

## 5. Ownership split

Backend/repository owns:
- publication membership;
- ordering;
- stable ID;
- canonical slug;
- game name/short name;
- supported platforms;
- game-entity catalog description;
- cover image URL when available;
- optional authoritative tournament count.

Frontend owns:
- page-level final Persian content around the catalog;
- card layout/presentation;
- localization/formatting;
- accessibility/responsive behavior;
- canonical `/games` and robots policy;
- crawlable links to canonical `/games/$slug` and `/tournaments?game=<gameId>`;
- deterministic fixture data for dev/test/visual QA only.

## 6. Production adapter behavior

Frontend production adapter targets `GET /api/v1/games/` and runtime-validates the payload.

Production MUST fail closed when:
- API base URL is missing;
- HTTP response is unsuccessful;
- payload violates the strict public contract.

Production MUST NOT silently replace such failures with local fixture games.

## 7. Security / privacy

Public response must not contain:
- phone/email;
- private account/profile fields;
- group/permission/role internals;
- moderation evidence;
- payment/refund/settlement data;
- private disputes/challenges;
- secrets or operational configuration.

Everything mutable/business-significant visible in the frontend remains backend-owned according to `docs/ENGINEERING_RULES.md`.

## 8. F02 compatibility

F02 `/games/$slug` is a frozen frontend route and its canonical identity must not be broken by F18 list implementation.

The catalog list and future detail API must agree on stable game identity and canonical slug. P02 must not introduce separate incompatible slug/key systems for list versus detail.

## 9. Documentation-only boundary

This alignment may change only:
- `PROJECT_CONTINUITY.md`;
- `docs/F18_PUBLIC_GAME_CATALOG_CONTRACT.md`.

Forbidden in this alignment:
- Python;
- models/migrations;
- serializers/views/URLs;
- dependencies;
- settings;
- `docs/PHASE_REGISTRY.md`;
- phase reordering.

Runtime implementation belongs to P02 and requires its own accepted Issue/branch/official-source audit/code/tests/CI/PR/closeout evidence.

Closing backend Issue #33 means this contract documentation is aligned. It does not mean `GET /api/v1/games/` is live.
