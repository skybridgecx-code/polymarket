# Phase 34B — Demo Workflow Validation Hardening

## Summary
Phase 34B hardened the local demo launcher validation script so the prepare-only workflow is checked more explicitly for reliability and common local failure modes.

Updated component:
- `scripts/validate_future_system_operator_ui_demo_launcher.sh`

Supporting docs/index updates:
- `docs/FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md`
- `.codex/phases/current_phase.md`

## What Was Hardened
- Added explicit step labels for each validation stage.
- Kept repo-root guard and launcher syntax check.
- Kept using existing Makefile targets (`future-system-operator-ui-demo-clean`, `future-system-operator-ui-demo-prepare`).
- Added `.tmp/demo-validation-sentinel` protection check to verify cleanup does not remove `.tmp` globally.
- Upgraded file checks from "exists" to "exists and non-empty":
  - `.tmp/future-system-operator-ui-demo/context_bundle.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`
- Added companion metadata content contract checks:
  - `review_status == "pending"`
  - `operator_decision == null`
  - `run_id == "theme_ctx_strong.analysis_success_export"` (resolved via `run_id` or `artifact.run_id`)
- Added review JSON content checks for expected run context:
  - `status == "success"`
  - `theme_id == "theme_ctx_strong"`
  - `export_kind == "analysis_success_export"`
- Preserved evidence protection checks:
  - `evidence/local-operator-ui` must still exist
  - file listing must remain unchanged
- Added bounded cleanup safety via EXIT trap:
  - removes only `.tmp/future-system-operator-ui-demo` and the script sentinel

## Failure Classes Caught Earlier
- Cleanup target accidentally deleting more than demo temp directory under `.tmp`.
- Context bundle or generated artifacts being empty/truncated.
- Companion metadata initialization drifting from expected defaults.
- Generated review JSON missing expected success/run context fields.
- Evidence package directory/listing changes during launcher validation.

## What This Intentionally Does Not Do
- Does not start Uvicorn or run browser/manual UI checks.
- Does not modify runtime app code, templates, or backend behavior.
- Does not modify test suites.
- Does not modify evidence screenshots.
- Does not remove `.tmp` globally.

## Commands
Primary command:

```bash
make future-system-operator-ui-demo-validate
```

Related commands used in the phase validation baseline:

```bash
bash -n scripts/launch_future_system_operator_ui_demo.sh
bash -n scripts/validate_future_system_operator_ui_demo_launcher.sh
test -x scripts/validate_future_system_operator_ui_demo_launcher.sh
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

## Validation Results (Phase 34B)
- Launcher syntax check passed.
- Hardened validation script syntax and executable checks passed.
- `make future-system-operator-ui-demo-validate` passed with hardened checks.
- Post-validation cleanup expectation passed (`.tmp/future-system-operator-ui-demo` removed, `.tmp` preserved).
- `evidence/local-operator-ui` existence check passed.
- Focused `pytest`, `ruff`, and `mypy` checks passed.
- Known non-blocking warning remains: `PendingDeprecationWarning` from `starlette.formparsers`.

## Boundaries Preserved
- No `src/polymarket_arb/*` changes.
- No runtime behavior changes.
- No DB/queue/jobs/notifications/scheduling/trading/execution behavior added.
- No committed evidence screenshot changes.
