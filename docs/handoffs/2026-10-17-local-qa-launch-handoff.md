# Turnoment — local QA handoff and five-day launch plan

Updated: 2026-10-17. Status: IN PROGRESS / LOCAL ACCEPTANCE PARTIAL. No production deployment or complete-project acceptance is claimed.

## Read first
This report supplements older PROJECT_CONTINUITY sequencing. Verify live repository refs, open PRs and the latest Windows source before implementation. Do not restart the project, reseed the existing QA database, overwrite local fixes with main, or assume this documentation uploads the Windows source.

## Source identity and synchronization gap
GitHub main inspected for this documentation checkpoint:
- frontend sajadkhavas/turnoment: d367aa23c6b33e4aaa05192d510d7c9122b5472c
- backend sajadkhavas/turnoment-backend: 0663ee42849ebab4ccb432611de8e2bcba9690aa

Historical Windows commits reported by user, remote availability NOT verified:
- frontend ff0625f on fix/local-session-result-confirmation-20261012-194202.
- backend 9390c86 on fix/local-result-confirmation-20261012-194202.

Additional changes were delivered through turnoment-player-events-batch1.zip and inline fixes. Latest exact Windows heads/diff have NOT been collected after these edits. The code is not certified synchronized or merged by this handoff. FIRST engineering task: collect latest sanitized frontend/backend source and git status/head, reconcile on dedicated branches, review diff and run gates. Do not blindly cherry-pick historical SHAs.

## Implemented/delivered locally
- SSR request-scoped session-cookie forwarding; result confirmation eligibility and UI; match-list result links; challenge start/finish lifecycle.
- Result ratingDelta reads AppliedMatchEvent after authoritative finalization consumption.
- Transactional inbox notifications for challenge/match/result/dispute/team/registration/check-in/tournament/achievement/rating events; target routes.
- Browser push subscription API, service worker, preference controls, unread count, retrying delivery worker; SMS delivery seam remains DISABLED, no live Kavenegar integration.
- Push setup/load scripts and process_player_events command.
- User-row locking in apps/challenges/services.py changed to select_for_update(no_key=True) after concurrent accept/cancel test exposed a deadlock. Challenge locking preserved.
- vite.config.ts explicit @ alias via node:url fileURLToPath; prior inline regex patch was invalid and was replaced from backup. Latest source must be inspected.

## Acceptance evidence and limits
Automated evidence from user-uploaded logs (not GitHub CI):
- Initial full backend run: 171 passed, 1 deadlock failure.
- After lock fix, full Verify-Local.ps1 reached LOCAL_VERIFICATION_PASSED (backend suite + frontend typecheck/contracts/build, lint/check/migration-drift checks in script). Obtain exact run counts/source SHA in next reconciliation.
- Earlier package preparation: frontend 25 contract scripts/typecheck/build and backend static checks passed. Original package-preparation environment had no PostgreSQL; later Windows run supplied database evidence.
Manual acceptance reported by user on Oct 13:
- Two seeded players log in; login request sometimes spends too long on sending code. OPEN, not fixed.
- Challenge invite/accept -> ready -> start -> finish -> report -> opponent confirmation works.
- Real Windows/browser push delivered; notifications also persisted in site inbox. Invite/accepted/ready are distinct messages, not established duplicates.
- Dispute created with evidence upload; both players see disputed state, result confirmation blocked, notifications delivered.
- Admin superuser was created successfully (credentials private).
- Admin review/resolution of dispute NOT yet tested.
- Numeric ratingDelta on both player result pages NOT yet confirmed.
- Reject/cancel/expiry, third-user privacy, full teams/tournaments/hosting and other modules are NOT fully accepted.
- No live SMS, public VPS acceptance, full security/responsive acceptance or production readiness signoff.

## Local environment — Windows
Root: C:\Users\sajad\Turnoment-QA-20261012-161153
Python .venv: 3.12.10; user also has Python 3.14. Node 24.21.0, Bun 1.4.2.
PostgreSQL container: turnomentqa20261012161212-postgres-1, host 127.0.0.1:55439, database turnoment_e2e.
Redis container: turnomentqa20261012161212-redis-1, host 127.0.0.1:56389.
Do NOT start unrelated project containers or recreate volumes.
DB_USER/DB_PASSWORD must be restored privately from container configuration or approved local config; do not print them. Generated backend-console-otp.ps1 / player-events.ps1 did not reliably persist DB env: a fresh shell silently used 5432/turnoment and timed out. Need one durable launcher restoring correct QA env for backend AND worker.
Processes:
- backend 8000: manage.py runserver 127.0.0.1:8000 --noreload, config.settings.local.
- frontend 4174: dev/preview encountered Nitro unavailable, alias and aborted ECONNRESET problems. Direct node .output/server/index.mjs with NITRO_HOST=127.0.0.1, NITRO_PORT=4174 served /login HTTP 200. This is a workaround; dev reliability remains OPEN.
- ingress proxy 4173: backend/scripts/b99_local_proxy.mjs. Browser canonical local entry http://127.0.0.1:4173.
- worker: manage.py process_player_events, same QA DB env and Web Push config as backend.
Web Push config path: C:\Users\sajad\turnoment-webpush\config.json and adjacent private key. NEVER upload/commit these files. Load-WebPush.ps1 loads process env. Do not rotate keys merely for restart.
Old session corruption was observed after restart; clearing site data allowed login. OTP latency root cause is not established.
Admin :8000 and player :4173 share hostname cookies across ports: use separate browser profiles for admin/Alpha/Bravo. Zero-match list after admin login may reflect wrong identity; no data loss was established.

## Ratings season incident
Seed season b99-browser-season originally ended 2026-10-13 12:45:20 UTC.
Two later FinalizedResultEvent rows were blocked by "Finalization requires exactly one configured season".
In verified local DEBUG / *_e2e database only, sole season end was extended to 2026-10-20 16:15:16.850199 UTC.
Subsequent drain returned processed: 0; user received notifications. Likely another worker consumed events, but confirm AppliedMatchEvent and both numeric deltas. Do not fabricate ratings or re-submit results. Workers may have been duplicated across windows.
Future production season lifecycle and blocked-event observability need completion; no automatic arbitrary production extension.

## Open dispute
ID: 348ee8fe-14b6-4da3-b1e0-99b4d89261f2.
Wrong-score reason, statement submitted, a random test image uploaded. This only verifies upload, not evidence validity.
Missing UX: result-confirmation page has no create-dispute link while awaiting-confirmation; existing link appeared only after disputed. Add eligible "اعتراض به نتیجه" action via contract, preserve backend authorization.
Next admin task: review this exact case through authorized admin operations, verify resolution, player projections, notifications, rating/event behavior and audit trail. Inspect available decisions before choosing; do not assume corrected-score support.

## Five-day launch plan agreed with user
Deadline target, not a guarantee of completion. No new redesign/features added.
Day 1: source reconciliation, durable local launcher, login/session/dev issues, dispute link, ratings evidence and admin dispute lifecycle.
Day 2: full free tournament lifecycle: publish/register/capacity/cancel/check-in/bracket/progression/completion.
Day 3: teams/membership/achievements/profile/settings/rankings/centers/hosting with real data.
Day 4: notification coverage/Kavenegar integration, permissions/security/mobile, staging deployment with HTTPS/logs/backups/workers.
Day 5: server end-to-end acceptance, blocker fixes, restore/rollback rehearsal, production release.
Need domain/server/SMS access. Financial execution remains deferred per B00: no payments/wallet/payout/refund settlement unless separately scoped and fully accepted; disable unsupported money features.
Completion per module: code reviewed, tests passed, manual role scenarios accepted, Git commit/PR/CI recorded. No blanket DONE claims.

## Exact NEXT for a new chat
1. Read this report + repository protocols and verify actual refs.
2. Obtain latest sanitized Windows source, status and exact heads; source excludes .env, private keys, databases, .venv, node_modules, generated build/output, secrets. Preserve local data.
3. Reconcile fixes on branches; establish repeatable launcher and single worker.
4. Confirm rating deltas / event application, finish admin dispute case, add dispute-entry UX, investigate OTP latency.
5. Continue five-day module test matrix; track results honestly. Do not deploy without user's server authorization.
