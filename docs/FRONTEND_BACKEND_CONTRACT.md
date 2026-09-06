# Frontend ↔ Backend Contract Baseline

Frontend source: `sajadkhavas/turnoment`

Accepted frontend baseline through P01:

`8d5736d788235e3e99765a5332f79f0cba861482` — `Added full ranking page`

This document prevents a frontend screen from being considered product-complete while its mutable data/business behavior has no backend owner.

## Existing / active frontend surfaces

| Frontend surface | Backend owner | Contract |
|---|---|---|
| `/` homepage | discovery/content | planned `GET /api/v1/discovery/home/` |
| `/tournaments` | tournaments | planned `GET /api/v1/tournaments/` |
| `/tournaments/{id}` | tournaments/registrations | planned detail + registration commands |
| `/games` | games | planned `GET /api/v1/games/` |
| `/centers` | gaming_centers | planned `GET /api/v1/gaming-centers/` |
| `/centers/{id}` | gaming_centers | planned `GET /api/v1/gaming-centers/{id}/` |
| `/ranking` | rankings | planned `GET /api/v1/rankings/` |
| `/rules` | rulesets/game policies | planned `GET /api/v1/rulesets/` |
| `/host` | gaming_centers/onboarding | planned application command |
| `/login` | accounts | P01 OTP/session contract below |
| `/register` | accounts | P01 OTP/session contract below |
| legacy `/dashboard` | player dashboard | private identity via P01; dashboard projection planned later |
| legacy `/dashboard/profile` | accounts/player profile | `PATCH /api/v1/auth/me/profile/` |

## P01 — Authentication / identity contract

The current Lovable `/login` and `/register` forms still display password-oriented legacy UI. They are UI scaffolding only and MUST converge onto one phone-OTP flow; the frontend must not invent password account behavior for players.

### Same-origin web flow

1. `GET /api/v1/auth/csrf/` — establishes/returns CSRF token.
2. `POST /api/v1/auth/otp/request/` — canonical Iran mobile input; returns opaque `challenge_id`, expiry and resend timing.
3. `POST /api/v1/auth/otp/verify/` — verifies six-digit OTP, creates player account/profile when first seen, and establishes Django session.
4. `GET /api/v1/auth/me/` — private current-account projection.
5. `PATCH /api/v1/auth/me/profile/` — mutable player profile fields.
6. `POST /api/v1/auth/logout/` — terminates authenticated session.
7. `GET /api/v1/players/{gamer_tag}/` — anonymous-safe public player projection.

OTP request/verify are CSRF-protected. Frontend must send the CSRF token on unsafe same-origin requests and include session credentials after verification.

### P01 ownership

Backend-authoritative:
- canonical phone identity;
- account active state;
- OTP expiry, request cooldown/window and attempts;
- session authentication state;
- gamer-tag uniqueness;
- platform roles/permissions;
- private/public identity boundary.

Frontend-owned:
- OTP input presentation;
- transitions/animations/countdown rendering;
- visual onboarding layout.

Public player responses never contain `phone`, `email`, `interview_opt_in`, group names or permission data.

## Planned frontend surfaces already approved

| Frontend surface | Backend owner | Planned contract |
|---|---|---|
| `/games/{slug}` | games | `GET /api/v1/games/{slug}/` |
| `/players/{username}` | players | now backed by P01 public player identity; competitive stats expand later |
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

1. Display names are not relational keys. APIs use stable identifiers; public entities may additionally use slugs/gamer tags.
2. Frontend never calculates authoritative rating, financial totals, settlement, tournament lifecycle or final match result.
3. `Tournament Rating` and `Challenge Rating` are separate backend concepts.
4. Challenge eligibility is backend-authoritative; the approved rule is 30 finalized valid matches, regardless of wins/losses.
5. Public SEO pages receive server-fetchable backend data so TanStack Start can SSR meaningful HTML.
6. Backend-controlled SEO fields may include slug, SEO title, description, index policy, canonical policy, OG media and publication state.
7. Mock data is temporary UI scaffolding, not durable schema.
8. When Lovable adds a new mutable field or action, its backend owner and contract must be added here before the associated phase closes.
