# Frontend ↔ Backend Contract Baseline

Frontend source: `sajadkhavas/turnoment`

Accepted frontend baseline for P00:

`8d5736d788235e3e99765a5332f79f0cba861482` — `Added full ranking page`

This document prevents a frontend screen from being considered product-complete while its mutable data/business behavior has no backend owner.

## Existing / active frontend surfaces

| Frontend surface | Backend owner | Planned contract |
|---|---|---|
| `/` homepage | discovery/content | `GET /api/v1/discovery/home/` |
| `/tournaments` | tournaments | `GET /api/v1/tournaments/` |
| `/tournaments/{id}` | tournaments/registrations | `GET /api/v1/tournaments/{id}/` + registration commands |
| `/games` | games | `GET /api/v1/games/` |
| `/centers` | gaming_centers | `GET /api/v1/gaming-centers/` |
| `/centers/{id}` | gaming_centers | `GET /api/v1/gaming-centers/{id}/` |
| `/ranking` | rankings | `GET /api/v1/rankings/` |
| `/rules` | rulesets/game policies | `GET /api/v1/rulesets/` |
| `/host` | gaming_centers/onboarding | `POST /api/v1/gaming-center-applications/` |
| legacy `/login` / `/register` | accounts | auth contract to be defined in auth phase |
| legacy `/dashboard` | player dashboard | `GET /api/v1/me/dashboard/` after redesign |

## Planned frontend surfaces already approved

| Frontend surface | Backend owner | Planned contract |
|---|---|---|
| `/games/{slug}` | games | `GET /api/v1/games/{slug}/` |
| `/players/{username}` | players | `GET /api/v1/players/{username}/` |
| `/dashboard/tournaments` | registrations/tournaments | `GET /api/v1/me/tournaments/` |
| `/matches/{id}` | matches | `GET /api/v1/matches/{id}/` + state commands |
| `/matches/{id}/result` | results | result submit/confirm endpoints |
| `/matches/{id}/dispute` | disputes | dispute create/read/evidence endpoints |
| `/challenges` | challenges | list/create/respond endpoints |
| `/challenges/{id}` | challenges | detail/state endpoints |
| `/rivalries/{id}` | rivalries | `GET /api/v1/rivalries/{id}/` |
| `/live` | matches/tournaments | live projection contract |
| `/stories` | stories | published content contracts |
| venue dashboard surfaces | gaming_centers/tournament ops | authenticated venue operator contracts |

## Contract rules

1. Display names are not relational keys. APIs use stable identifiers; public entities may additionally use slugs/usernames.
2. Frontend never calculates authoritative rating, financial totals, settlement, tournament lifecycle or final match result.
3. `Tournament Rating` and `Challenge Rating` are separate backend concepts.
4. Challenge eligibility is backend-authoritative; the approved rule is 30 finalized valid matches, regardless of wins/losses.
5. Public SEO pages receive server-fetchable backend data so TanStack Start can SSR meaningful HTML.
6. Backend-controlled SEO fields may include slug, SEO title, description, index policy, canonical policy, OG media and publication state.
7. Mock data is temporary UI scaffolding, not durable schema.
8. When Lovable adds a new mutable field or action, its backend owner and contract must be added here before the associated phase closes.
