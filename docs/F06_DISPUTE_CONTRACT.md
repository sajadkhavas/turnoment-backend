# F06 — Match Dispute Frontend ↔ Backend Contract

Status: `PLANNED CONTRACT / FRONTEND MOCK / BACKEND PENDING`

Backend owner: `disputes`

Frontend route: `/matches/$id/dispute`

Frontend F06 START_SHA: `0407a925974d50b4a75af292231bacb48c66eb38`

Backend alignment START_SHA: `93d4158e55ebe5d4cb0e724c84104ddd9fbf0c17`

Tracking:
- frontend Issue `sajadkhavas/turnoment#47`
- backend alignment Issue `#15`

This document refines the already-reserved Dispute surface. It is a contract only. It does not implement disputes/matches/results Python code, migrations, moderation, storage, or API runtime. Backend NEXT remains `P02 — Games / Catalog Foundation`.

## Planned endpoints

Read:

`GET /api/v1/matches/{matchId}/dispute/`

Create:

`POST /api/v1/matches/{matchId}/dispute/`

Evidence:

`POST /api/v1/matches/{matchId}/dispute/{disputeId}/evidence/`

No dispute withdrawal/cancel command is part of F06. A future transition requires an explicit backend-owned contract before frontend exposure.

## Authentication / authorization / CSRF

- Django Session Authentication is required.
- Browser requests use `credentials: include`.
- Frontend Session route guards are UX/navigation only.
- Backend independently authorizes the authenticated participant against Match and dispute scope for every read/write.
- Unsafe create/evidence requests consume the P01 CSRF bootstrap contract and require `X-CSRFToken`.
- No localStorage bearer token is introduced.

## Read projection

```text
matchId
revision                         # opaque backend concurrency token
disputeState                     # eligible | open | under-review | resolved | unavailable
unavailableReason?               # only when unavailable
player { participantId, displayTag }
opponent { participantId, kind, displayTag }
game { gameId, name }
competition
  kind                           # tournament | challenge
  competitionId
  title
  tournamentSlug?                # tournament only
  roundLabel                     # tournament string; challenge null
venue? { gamingCenterId, name, city }
startsAt                         # offset-aware ISO datetime
timezone                         # IANA timezone
formatLabel
result
  state                          # awaiting-confirmation | disputed | finalized | void
  reportedScore? { playerScore, opponentScore }
  finalResult?                   # only when finalized; backend-authoritative
policy
  allowedReasons[]               # stable reason enum values
  minStatementLength
  maxStatementLength
  evidence
    enabled
    maxFiles
    maxFileBytes
    allowedMimeTypes[]           # browser selection hints only

dispute?                         # required for open/under-review/resolved
  disputeId
  status                         # open | under-review | resolved
  reason
  statement
  createdAt
  canAddEvidence                 # backend-authoritative
  evidence[]
    evidenceId
    fileName                     # safe display name only
    contentType
    sizeBytes
    uploadedAt
  resolution?                    # required only when resolved
    decision                     # upheld | rejected | adjusted | voided | no-action
    summary
    resolvedAt
```

### Read integrity

- `eligible` and `unavailable` expose no current dispute.
- `open`, `under-review`, and `resolved` require current dispute and matching status.
- `resolved` requires resolution and never accepts more evidence.
- resolution is absent for non-resolved state.
- evidence count never exceeds backend policy.
- disabled evidence policy exposes no evidence mutation capability.
- final score/outcome/rating truth appears only through backend-authoritative finalized result data.
- frontend never derives eligibility, moderation decision, corrected result, rating impact, or lifecycle from local values.

## Stable reason codes

Initial frontend contract recognizes:

- `incorrect-score`
- `rule-violation`
- `no-show`
- `technical-issue`
- `unsportsmanlike-conduct`
- `other`

Backend implementation owns which subset is allowed for a specific Match through `policy.allowedReasons`; frontend labels are presentation only.

## Create command

JSON body:

```text
revision
reason
statement
```

Header:

`Idempotency-Key: <opaque-key-per-logical-attempt>`

Backend requirements before live implementation:

- atomically re-check participant authorization and dispute eligibility;
- validate reason against current policy;
- validate normalized statement length/content policy;
- enforce persistent/transaction-safe idempotency;
- fail closed on conflicting key reuse;
- use opaque revision for stale detection;
- never let frontend state force dispute eligibility.

Typed outcomes:

`accepted`
- `matchId`
- current `revision`
- authoritative current dispute

`validation_error`
- reason/statement/form messages

`stale`
- current opaque `revision`

`unavailable`
- `not-eligible | already-resolved | window-closed | cancelled`

`already_open`
- `matchId`
- current `revision`
- authoritative current dispute

## Evidence upload command

Multipart body:

```text
revision
file
```

Header:

`Idempotency-Key: <opaque-key-per-logical-attempt>`

Backend security boundary:

- browser `accept` / `Content-Type` are hints only and MUST NOT be trusted as file-security truth;
- enforce authorization and `canAddEvidence` atomically;
- enforce actual file type/signature allowlist, file count and byte limits server-side;
- sanitize/replace storage names and store outside unsafe public execution paths;
- evidence access remains private/authorized; this contract does not create a public file URL;
- apply malware/sandbox/content scanning appropriate to the deployment before evidence is made available;
- protect upload with CSRF and request-size limits;
- define cleanup/retention policy in owning backend implementation.

Typed outcomes:

`accepted`
- `matchId`
- `disputeId`
- new/current `revision`
- authoritative evidence metadata

`validation_error`
- file/form message

`stale`
- current opaque `revision`

`unavailable`
- `not-open | review-locked | resolved | quota-reached | uploads-disabled`

`already_uploaded`
- same identity/metadata shape as accepted for idempotent retry

## Moderation / result boundary

F06 never owns moderation truth in the frontend. Backend alone owns:

- whether dispute can be opened;
- state transition `open → under-review → resolved`;
- whether more evidence may be added;
- resolution decision/summary;
- any result correction, voiding, winner/final state, rating recalculation, bracket effects or downstream consequences.

Those effects must be implemented transactionally in the owning backend phases and surfaced as authoritative projections.

## Integration gate

Until the disputes/results/matches backend slice implements these endpoints, permissions, concurrency/idempotency, evidence security/storage, moderation transitions and tests under the mandatory backend phase protocol:

`FRONTEND MOCK / BACKEND PENDING`

A final frontend route is not evidence that these APIs are live.
