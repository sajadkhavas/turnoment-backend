# Mandatory Phase Completion Protocol

This file is a root-level project rule and MUST be read before starting or continuing any backend phase.

## Non-negotiable rule

The chat/agent responsible for a phase is also responsible for recording that phase's final state in GitHub. A phase is **not complete** merely because code exists or tests pass.

Before a phase may be reported as `DONE`, the responsible chat/agent MUST:

1. Work on a dedicated phase branch. Never do feature work directly on `main`.
2. Create or use the phase-specific GitHub Issue as the execution record.
3. Record the exact `START_SHA`, active frontend baseline/contract SHA, branch, scope and acceptance gates.
4. Review authoritative upstream documentation relevant to that phase and record the decisions in `docs/OFFICIAL_SOURCES.md`.
5. Implement the full accepted scope, migrations, tests and documentation.
6. Run the repository quality gate and resolve failures instead of weakening the gate.
7. Open a PR, review the diff, resolve blockers/review threads, and merge only after CI is green.
8. After implementation merge, update **both** the phase section in `docs/PHASE_REGISTRY.md` and the phase-specific GitHub Issue.
9. The registry closeout record MUST contain: `START_SHA`, implementation `END_SHA`, final reviewed implementation SHA, implementation PR, implementation/pre-merge CI run(s), implementation merge SHA, closeout branch/PR reference, open review-thread count, and the closeout status that is true at the time that registry content is created.
10. After the closeout/freeze PR is merged, the phase-specific GitHub Issue MUST be updated with the exact closeout merge SHA (the frozen `main` SHA) and the final post-closeout `main` CI run. Once that CI is green, the Issue is the authoritative terminal evidence for `DONE / MERGED / FROZEN`.
11. Do not create recursive documentation-only PRs merely so a file can contain the SHA of the commit that contains that same file. A Git commit cannot self-record its own SHA because changing the recorded SHA changes the commit hash. The terminal closeout SHA and its post-merge CI therefore belong in the phase Issue after the merge.
12. Close the phase Issue only as `completed` after the terminal evidence above is recorded and final `main` CI is green.
13. If any required gate is pending, report the real status (`IN PROGRESS`, `BLOCKED`, `READY TO MERGE`, or `MERGED / CLOSEOUT IN PROGRESS`) and do **not** claim the phase is done.

## Source of truth

- Phase history and non-recursive closeout snapshot: `docs/PHASE_REGISTRY.md`
- Per-phase execution evidence and terminal freeze SHA/CI: the phase-specific GitHub Issue
- Frontend↔Backend ownership: `docs/FRONTEND_BACKEND_CONTRACT.md`
- Engineering rules: `docs/ENGINEERING_RULES.md`
- Official references: `docs/OFFICIAL_SOURCES.md`

This protocol applies to every future chat/agent working on this repository.
