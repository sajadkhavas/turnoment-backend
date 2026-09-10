# F12 — Player Rivalries Hub Cross-Repo Contract

Status: `PLANNED CONTRACT / DOCUMENTATION ONLY`

Frontend route: `/dashboard/rivalries`

Frontend workstream: `F12 — Player Rivalries Hub`

Frontend tracking Issue: `sajadkhavas/turnoment#65`

Backend tracking Issue: `#21`

Backend START_SHA: `3fb421cf2c85d94753ddf9352d8bc1134358847a`

Runtime status: `FRONTEND MOCK / BACKEND PENDING`

Backend NEXT remains: `P02 — Games / Catalog Foundation`

## 1. Purpose and bounded ownership

F12 defines the future private current-player Rivalries Hub projection needed by `/dashboard/rivalries`. It is a read-only aggregate view. This documentation does **not** implement a rivalries model, serializer, view, URL registration, migration, task, cache, or any other backend runtime slice.

A rivalry row represents one backend-defined current-player/opponent/game relationship. The backend owns whether that relationship exists and all aggregate competitive truth shown for it. The frontend MUST NOT construct authoritative rivalry rows by grouping local Match history.

Backend remains authoritative for:
- current-player rivalry membership;
- stable `rivalryId` identity;
- stable opponent and game identity;
- finalized valid head-to-head match counts;
- player wins, opponent wins and draws;
- rivalry edge (`player-leading | tied | opponent-leading`);
- latest finalized valid encounter and its score/outcome;
- list summary, filtering, ordering and pagination.

Frontend may:
- validate URL navigation state before sending it;
- localize labels and format supplied timestamps;
- choose responsive visual hierarchy;
- render the authoritative aggregate projection;
- present deterministic fixtures through the same repository interface for QA.

Frontend MUST NOT:
- derive rivalry membership from raw Match rows;
- count void/cancelled/unfinalized matches as finalized rivalry encounters;
- derive challenge eligibility, Challenge Rating or Tournament Rating from rivalry data;
- introduce wager/stake mechanics;
- create friend/block/social-graph state;
- invent a Rivalry Detail URL or mutation flow in F12.

## 2. Authentication / authorization

The endpoint is private and scoped to the authenticated current player.

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Backend resolves the current player from the authenticated session; no browser-supplied player ID controls ownership.
- Frontend dashboard access policy is UX/navigation only; backend authorization remains mandatory.
- No localStorage/sessionStorage bearer-token authentication is introduced.

F12 is read-only, so it defines no CSRF-protected mutation command.

## 3. Planned endpoint

`GET /api/v1/me/rivalries/`

Optional query parameters:
- `kind=player|team`; absence means all opponent kinds;
- `game=<stable-game-id>`; relation key is stable game identity, never display name;
- `sort=recent|most-played`; absence means `recent`;
- `page=<positive-integer>`; absence means page 1.

Backend query validation remains authoritative even though the frontend validates URL state first.

## 4. Response projection

```text
player
  playerId
  gamerTag

summary
  totalRivalries
  totalFinalizedMatches
  playerLeading
  tied
  opponentLeading

games[]
  gameId
  name

items[]
  rivalryId
  opponent
    participantId
    kind                        # player | team
    displayTag
  game
    gameId
    name
  headToHead
    totalFinalized
    playerWins
    opponentWins
    draws
    edge                        # player-leading | tied | opponent-leading
  lastEncounter
    matchId
    finalizedAt                 # offset-aware ISO datetime
    timezone                    # IANA timezone
    playerScore
    opponentScore
    outcome                     # win | loss | draw
    competition
      kind                      # tournament | challenge
      competitionId
      title

pagination
  currentPage
  totalPages
  totalItems
```

`lastEncounter` is required for every rivalry row because a rivalry row cannot exist without at least one finalized valid encounter under this contract.

## 5. Aggregate integrity law

Only finalized, valid, non-void encounters contribute to F12 head-to-head aggregates.

For each item:
- `totalFinalized >= 1`;
- `playerWins + opponentWins + draws = totalFinalized`;
- `edge=player-leading` only when `playerWins > opponentWins`;
- `edge=opponent-leading` only when `opponentWins > playerWins`;
- `edge=tied` only when `playerWins = opponentWins`;
- `lastEncounter.outcome=win` requires `playerScore > opponentScore`;
- `lastEncounter.outcome=loss` requires `playerScore < opponentScore`;
- `lastEncounter.outcome=draw` requires equal scores.

Void/cancelled/unfinalized Match records do not contribute to these counts and are not exposed as `lastEncounter`.

List-level summary, ordering, tie-breakers and pagination are backend-owned. The frontend must not recompute them from the current page of items.

## 6. Sort semantics

`recent`:
- ordered by authoritative `lastEncounter.finalizedAt` descending;
- backend applies a deterministic stable tie-breaker.

`most-played`:
- ordered by authoritative `headToHead.totalFinalized` descending;
- backend applies a deterministic stable tie-breaker.

The frontend may request a sort mode but does not perform an authoritative resort of returned data.

## 7. UI states supported by this contract

The final F12 frontend can represent:
- loading/pending;
- authenticated populated state;
- all-empty state when the player has no rivalry projection;
- filtered-empty state;
- load error/retry;
- unauthenticated/session-expired redirect;
- game/opponent-kind/sort URL navigation;
- pagination.

No write/pending-success mutation state is required because F12 is read-only.

## 8. Rivalry Detail boundary

An older product baseline reserves a future Rivalry Detail concept, but F12 does not create or claim that route. No dead link is rendered from the F12 Hub.

A future detail workstream must independently define its stable route identity, authorization, data contract, states, tests and acceptance chain before a detail link becomes active.

## 9. Competitive invariants retained

- Tournament Rating and Challenge Rating remain separate domains;
- Challenge unlock remains 30 finalized valid matches, not wins;
- F12 rivalry aggregates do not determine Challenge unlock or rating eligibility;
- no wager/betting/stake mechanics are introduced;
- frontend never determines finalized result/rating/dispute/challenge truth.

## 10. Runtime / phase-order gate

This file is cross-repo alignment only.

Until an owning backend phase implements and permission-tests the rivalry aggregate projection and endpoint under `PHASE_COMPLETION_PROTOCOL.md`:

`FRONTEND MOCK / BACKEND PENDING`

F12 documentation alignment does not start or reorder backend phases. Backend NEXT remains `P02 — Games / Catalog Foundation`.
