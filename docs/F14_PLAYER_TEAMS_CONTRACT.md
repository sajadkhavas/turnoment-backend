# F14 — Player Teams Hub Contract

Status: `IN PROGRESS — DOCUMENTATION / CROSS-REPO ALIGNMENT`

Frontend workstream: `sajadkhavas/turnoment#71`

Frontend route: `/dashboard/teams`

Backend START_SHA: `ddfdceaa9746cc6a60ad2b5e18e630c53904f00c`

Runtime truth: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains `P02 — Games / Catalog Foundation`.

## 1. Scope

This document reserves the production read contract required by the final private F14 Player Teams Hub. It does not start or reorder a backend runtime phase and does not claim that a Teams Django domain exists yet.

Planned authenticated endpoint:

`GET /api/v1/me/teams/`

F14 is read-only. No team management mutation endpoint is introduced by this workstream.

Existing Turnoment truth already establishes stable team identity for tournament participation (`teamId`, `teamName`), current-player team role `captain | member`, and team member count in team-registration context. Tournament/team eligibility remains backend-owned.

## 2. Authentication / authorization

- Django Session Authentication is the web authentication truth.
- Browser requests use `credentials: include`.
- The endpoint is private and server-authorized for the current player.
- Requested team selection is resolved only within the authenticated player's permitted memberships; it MUST NOT expose another team's private roster merely because a stable ID was guessed.
- Frontend route access checks are UX/navigation boundaries only.
- No localStorage/sessionStorage bearer token is introduced.

## 3. Query contract

Optional query parameters:

- `team=<stable-team-id>`; absence lets the server/repository choose the authoritative default current-player membership when one exists.
- `page=<positive-integer>`; absence means roster page 1.

Frontend validation is navigation convenience only. Backend validation and object authorization remain authoritative.

A requested team not available in the current player's permitted membership projection resolves to `selectionState=unavailable`; the response MUST NOT distinguish whether an unauthorized external team exists.

## 4. Response projection

```text
player
  playerId
  gamerTag

summary
  totalTeams
  captainOf
  memberOf

memberships[]
  teamId
  name
  role                           # captain | member
  memberCount

selectionState                   # none | selected | unavailable
selectedTeam?                    # null unless selected
  teamId
  name
  currentPlayerRole              # captain | member
  memberCount
  roster[]
    playerId
    gamerTag
    role                         # captain | member
  rosterPagination
    currentPage
    totalPages
    totalItems
```

`memberships[]` is the current-player's authoritative team membership switcher projection. Display names are content; stable IDs are relational identity.

`selectionState=none` is used when the current player has no team memberships. `selectionState=selected` requires `selectedTeam`. `selectionState=unavailable` indicates the requested stable team ID is not available in this player's current membership projection and does not reveal external team existence.

## 5. Authoritative integrity

Server/repository owns:

- whether the current player belongs to any team;
- stable team ID/name for each current membership;
- current-player role `captain | member` for each membership;
- team member count;
- default/explicit selected-team resolution;
- roster membership and each roster member's stable player identity, gamer tag and role;
- summary counts;
- roster pagination.

Required integrity expectations:

- `summary.captainOf + summary.memberOf == summary.totalTeams`;
- membership team IDs are unique;
- a selected team must correspond to exactly one returned membership;
- `selectedTeam.currentPlayerRole` must match the current player's role on that membership;
- `selectedTeam.memberCount == selectedTeam.rosterPagination.totalItems`;
- `selectedTeam.rosterPagination.totalPages >= 1`;
- `selectedTeam.rosterPagination.currentPage <= selectedTeam.rosterPagination.totalPages`;
- roster player IDs are unique within a response page;
- when the current player appears on the returned roster page, their roster role must agree with `currentPlayerRole`;
- a selected team must contain exactly one captain in the full authoritative roster domain, even when the current roster page does not contain that captain;
- `selectionState=selected` requires `selectedTeam != null`;
- `selectionState=none|unavailable` requires `selectedTeam == null`;
- `selectionState=none` requires zero memberships and zero summary counts;
- `selectionState=unavailable` may still return the caller's other valid memberships for reset/navigation.

Frontend MUST NOT infer any of these truths from F03 tournament participation history, registration history, local cache, gamer-tag display values or member counts.

## 6. Frontend ownership

Frontend may own only presentation/navigation concerns:

- validated `team`/`page` URL state;
- final Persian labels and explanatory product copy;
- team membership switcher interaction;
- roster presentation and role labels;
- responsive/accessibility behavior;
- deterministic fixture adapter for development/test/visual QA behind the same repository interface.

Frontend MUST NOT:

- determine whether a player currently belongs to a team from tournament records;
- promote/demote a player or derive captaincy;
- infer tournament registration eligibility from team membership/member count;
- infer Challenge eligibility or rating truth;
- calculate a team ranking/rating;
- expose guessed team rosters by stable ID;
- invent a Team Detail route or arbitrary member-profile action as part of F14;
- mutate `/dashboard/challenges`.

## 7. Explicitly deferred team operations

The registry previously described this area broadly as “Team / Clan operations”. F14 intentionally narrows the accepted page to the evidence-supported read surface because no authoritative mutation policy/capability matrix is yet defined.

The following require an owning future domain phase/workstream before they can appear as real actions:

- create/rename/delete team;
- invite/request/accept/decline membership;
- remove/kick member;
- leave team;
- captain transfer/promotion/demotion;
- roster size limits;
- public/private team visibility;
- team rating/ranking;
- tournament or Challenge eligibility based on team composition.

A future mutation contract must define server-side authorization, capability projection, CSRF, stale/concurrency behavior, idempotency where relevant, and typed outcomes. F14 does not reserve those semantics prematurely.

## 8. Runtime / phase boundary

This alignment changes documentation only. It MUST NOT modify:

- Python application code;
- models or migrations;
- serializers, views or URLs;
- dependencies;
- `docs/PHASE_REGISTRY.md`;
- backend phase ordering.

Until an owning backend runtime phase implements and permission-tests this endpoint, runtime remains exactly:

`FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains exactly:

`P02 — Games / Catalog Foundation`.
