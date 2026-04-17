# Phase 34A — Demo Workflow Reliability Inventory

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-34a-demo-workflow-reliability-scope-lock`
- Phase: `34A — future_system demo workflow reliability inventory`
- Source checkpoint: current shipped local demo launcher workflow

## Sources Reviewed
- `Makefile`
- `scripts/launch_future_system_operator_ui_demo.sh`
- `scripts/validate_future_system_operator_ui_demo_launcher.sh`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `docs/FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md`
- `docs/PHASE_29E_DEMO_LAUNCHER_TRACK_CLOSEOUT.md`
- `docs/PHASE_30A_OPERATOR_UI_LAUNCHER_SMOKE_TESTS.md`
- `docs/PHASE_31E_RUN_DETAIL_UX_TRACK_CLOSEOUT.md`
- `docs/PHASE_32E_LIST_CREATE_UX_TRACK_CLOSEOUT.md`
- `docs/PHASE_33A_OPERATOR_UI_E2E_RUNBOOK_REFRESH.md`

## Current Demo Commands
- `make future-system-operator-ui-demo-validate`
- `make future-system-operator-ui-demo-prepare`
- `make future-system-operator-ui-demo`
- `PORT=8010 make future-system-operator-ui-demo`
- `make future-system-operator-ui-demo-clean`

## Current Generated Temp Paths
- `.tmp/future-system-operator-ui-demo/context_bundle.json`
- `.tmp/future-system-operator-ui-demo/operator_runs/`

## Current Expected Run ID
- `theme_ctx_strong.analysis_success_export`

## Current Known Warning
- `PendingDeprecationWarning` from `starlette/formparsers`

## Potential Brittle Points Observed In Prior Work
- `python-multipart` missing locally can block manual Uvicorn/form handling.
- port `8000` may already be in use.
- stale server / artifact-root mismatch can produce missing-run confusion.
- fixture input is not directly the final context bundle; launcher must construct a valid bundle.
- `.tmp` generated artifacts appear as untracked local files if cleanup is skipped.

## Current Reliability Guardrails Already Present
- launcher preflight checks for repo root, fixture presence, Python interpreter, and valid port.
- dependency check for `python-multipart` with explicit install command.
- deterministic context bundle generation from fixture case `strong_complete`.
- deterministic CLI artifact generation with `--initialize-operator-review`.
- bounded port preflight before Uvicorn startup.
- bounded cleanup target for `.tmp/future-system-operator-ui-demo` only.
- smoke validation script verifies expected files and ensures evidence directory listing is unchanged.

## Safe Reliability Opportunities (No Implementation In 34A)
- tighten stdout summaries so each workflow step and output location is more explicit.
- strengthen artifact verification around expected files and deterministic run id assumptions.
- improve failure guidance clarity for common setup faults (dependency, fixture, root config).
- add an optional no-browser CLI-only smoke pass for headless confidence checks.
- optionally write a bounded workflow status marker under `.tmp` to simplify post-run diagnostics.
