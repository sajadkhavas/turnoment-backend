# B06 — Private Teams / Achievements handoff

Implementation base: `ffe44e3d999479282115c4bebdb4f33b40f5a598`
Frontend contract: `1668109bae5ec7abb5e022e5857ffa65cc131501`

## Frozen read contracts

- `GET /api/v1/me/teams/?team=<UUID>&page=N`: exactly F14 private projection; unknown/outside IDs return `selectionState=unavailable` with no roster.
- `GET /api/v1/me/achievements/?status=&category=&sort=&page=`: exactly F13 private projection; only published definitions, no implicit awards, no fixture fallback.
- Both inherit SessionAuthentication/CSRF defaults; `IsAuthenticated` required.

## B06-owned management extensions

- `POST /api/v1/teams/` create with atomic captain membership.
- `POST /api/v1/teams/<UUID>/invites/` captain only; repeat pending invite returns 200 with stable ID.
- `GET /api/v1/me/team-invites/` recipient only, pending invitations only.
- `POST /api/v1/teams/invites/<UUID>/accept|decline/` recipient only, idempotent same-state replay; accept adds membership once.
- `POST /api/v1/teams/<UUID>/captain/` captain only, recipient must already belong.
- `POST /api/v1/teams/<UUID>/leave/` members only; captain cannot leave without transfer.

## Narrow integration contracts

`apps.teams.services.tournament_eligible_teams(user, tournament)` returns candidate captained team dicts with `id`, `name`, `memberCount`, `role`, and never authorizes tournament registration. Existing B05 setting
`TOURNAMENT_TEAM_ELIGIBILITY_HOOK="apps.teams.services.tournament_eligible_teams"` may be wired by B99 once authoritative eligibility and participant constraints are agreed. **B06 intentionally does not modify registration/team-hooks internals or activate team registration.**

`apps.achievements.services.record_progress(user=..., definition_id=..., event_key=..., increment=1)` is a trusted service-only exactly-once event consumer; no HTTP awarding, money, self-claim, points or tournament match result inference. B08/B09/B99 must supply authenticated source events and configure business-specific published definitions. Until then the achievements hub is legitimately empty.

Captains are DB-unique per team; creation and transfers preserve exactly one captain at every committed state. Invites and membership are DB-deduped, parent Team locked for competing writes, user row locked for achievement events. No public roster or private phone/email exposure.

## Shared-file edits

Only two necessary registrations: `config/settings/base.py` (2 installed apps) and `config/urls.py` (2 API routes). `docs/OFFICIAL_SOURCES.md` adds official-reference audit. No dependency or CI edits. B99 should reconcile these registrations by appending rather than replacing other workstreams.

FINANCIAL EXECUTION ADDED: NO
