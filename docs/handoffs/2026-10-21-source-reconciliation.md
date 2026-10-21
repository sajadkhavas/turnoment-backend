# Local QA source reconciliation — 2026-10-21

Status: PARTIAL / DRAFT; no merge, production readiness, or Windows runtime acceptance claimed.

- START_SHA: `0663ee42849ebab4ccb432611de8e2bcba9690aa` (verified cloned main).
- Branch: `sync/local-qa-20261021`.
- Input: user-uploaded `backend-changes.zip`, generated from local HEAD `9390c860f210c53ed72d4a720b6fe9f367eecaac` plus uncommitted changes.
- The patch includes the last local commit and tracked working-tree changes; allowlisted untracked source files are restored at their repository paths.
- Patch applied cleanly to current main. This is a source snapshot, not a redesign or certification of the new action boundaries.
- Backup files, seed JSON, egg-info, private configuration, database contents, dependencies and build output were excluded.
- Original Windows tree/database have not been modified by this reconciliation.

## Validation

Both: patch application and `git diff --check` passed.
Backend: 14 database-independent tests passed (phone normalization/validation and push endpoint validation). Ruff and Python compile passed; Django system checks passed; migration generation reports no changes, with migration-history verification unavailable because PostgreSQL is absent. Database suite and production checks pending.
Frontend: frozen Bun install, lint (0 errors / 6 existing UI fast-refresh warnings), production build, TypeScript typecheck and all 25 contract scripts passed.

## Open review items

- Direct HTTP calls in new UI actions must be reconciled with the typed repository/action architecture and tested.
- Missing awaiting-confirmation dispute entry remains open.
- Push logout/account-switch lifecycle needs explicit privacy acceptance; delivery retry and subscription ownership need further tests.
- Numeric rating deltas and the existing admin dispute case require real local database acceptance.
- Durable Windows launcher, one worker, OTP latency and frontend dev reliability remain open.
- The recorded QA season ended on 2026-10-20; inspect actual season/event state before new rating tests. No automatic extension or result replay authorized by this snapshot.

## Exact NEXT

1. Review this source-only reconciliation and run repository CI on the exact PR head.
2. Keep the user's original local source intact until reviewed source acceptance.
3. Finish the action contract/dispute-entry and push lifecycle review, then run role/privacy/concurrency tests.
4. Restore the existing Windows QA environment without reseeding; verify rating receipts and admin dispute lifecycle.
5. Continue the module acceptance matrix from the Oct 17 handoff (backend PR #82 / frontend PR #124).

## Publication status

Both GitHub push attempts were blocked by automatic approval review because publishing this local code payload to the two repositories needs explicit user authorization. No draft PR was created. Next publication requires user approval for these exact repositories and branch; no merge or deployment is included.
