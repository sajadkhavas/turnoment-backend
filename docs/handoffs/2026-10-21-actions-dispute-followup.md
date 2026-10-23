# Actions and dispute entry follow-up — 2026-10-21

Status: implementation complete for this bounded change; Windows/PostgreSQL acceptance pending.

Frontend START: d630ab292ac0206b918daba46a47a84a35c11aa9 (PR #126).
Backend START: c2f91d76663deb0ac6079fb4ad319053a1620793 (PR #83).
Working branch: fix/qa-actions-dispute-20261021; installation targets the existing Windows sync branch.

Changes: backend-owned canCreateDispute projection; awaiting-confirmation dispute link;
central typed match action repository with runtime-validated commands, CSRF bootstrap,
receipts and lifecycle identity/transition validation; confirmation double-click guard.
Authoritative services/permissions, result scores and rating/event consumption stay unchanged.

Validation: frontend lint (0 errors, 6 existing warnings), production build, TypeScript and
26 contract scripts passed. Added negative receipt/identity/state/CSRF tests and a backend
participant/outsider/disputed-state regression. Backend Ruff, compile, Django check and
14 database-independent tests passed. The new database regression has not yet run here:
PostgreSQL is unavailable in this environment. Previous PR CI passed both backend Python
versions before this follow-up; that is not certification of this new source.

Official references reviewed:
- https://tanstack.com/router/latest/docs/guide/data-mutations — refresh from server-owned state after mutations.
- https://www.django-rest-framework.org/api-guide/serializers/ — validate requests/responses at contract boundaries.
- https://docs.djangoproject.com/en/6.1/topics/db/transactions/ — keep database state changes within existing service transactions.
No redesign/public copy/SEO scope; existing RTL controls and private routes are preserved.

Kavenegar/OTP/login and B99 workflow unchanged at the user's request. B99 remains failed,
not waived or declared accepted. No financial execution or server deployment included.

Exact NEXT:
1. Apply the incremental package with checksum/head/content checks and backup.
2. Run Verify-Local.ps1 against the existing QA PostgreSQL container. pytest creates its own test database.
3. Commit only manifest-listed files on the existing sync branch and push from VS Code.
4. Check PR #126/#83 CI; manually verify the existing dispute and both rating deltas.
5. Continue remaining tournament/team/host/module/security acceptance; do not claim whole-project DONE.
