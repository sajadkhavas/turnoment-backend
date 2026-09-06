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
9. The final phase record MUST contain: `START_SHA`, implementation `END_SHA`, final reviewed phase SHA, implementation PR, CI run(s), implementation merge SHA, closeout/freeze PR and merge SHA when used, open review-thread count, and final status `DONE / MERGED / FROZEN`.
10. Close the phase Issue only as `completed` after the evidence above is recorded.
11. If any required gate is pending, report the real status (`IN PROGRESS`, `BLOCKED`, or `READY TO MERGE`) and do **not** claim the phase is done.

## Source of truth

- Phase history: `docs/PHASE_REGISTRY.md`
- Per-phase execution/evidence: the phase-specific GitHub Issue
- Frontend↔Backend ownership: `docs/FRONTEND_BACKEND_CONTRACT.md`
- Engineering rules: `docs/ENGINEERING_RULES.md`
- Official references: `docs/OFFICIAL_SOURCES.md`

This protocol applies to every future chat/agent working on this repository.
