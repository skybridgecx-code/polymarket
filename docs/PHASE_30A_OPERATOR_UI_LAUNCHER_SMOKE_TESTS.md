# Phase 30A — Operator UI Launcher Smoke Tests

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-30a-operator-ui-launcher-smoke-tests`
- Phase: `30A — operator UI launcher smoke tests`
- Source checkpoint: Phase 29E launcher track closeout

## What Was Added
- Added focused smoke validation script:
  - [scripts/validate_future_system_operator_ui_demo_launcher.sh](../scripts/validate_future_system_operator_ui_demo_launcher.sh)
- Added Makefile target:
  - `future-system-operator-ui-demo-validate`

## Exact Command
- `make future-system-operator-ui-demo-validate`

## What Smoke Validation Verifies
- launcher script syntax check:
  - `bash -n scripts/launch_future_system_operator_ui_demo.sh`
- bounded cleanup invocation:
  - `make future-system-operator-ui-demo-clean`
- deterministic prepare-only artifact generation:
  - `make future-system-operator-ui-demo-prepare`
- expected generated files exist:
  - `.tmp/future-system-operator-ui-demo/context_bundle.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`
- bounded cleanup behavior:
  - cleanup removes `.tmp/future-system-operator-ui-demo`
  - cleanup does not remove `.tmp` as a whole
- evidence guardrail:
  - `evidence/local-operator-ui` file listing remains unchanged

## What It Intentionally Does Not Do
- Does not start Uvicorn.
- Does not bind ports.
- Does not modify runtime app codepaths.
- Does not modify evidence screenshots.
- Does not run or add production trading/execution behavior.

## Generated Temp Paths
- `.tmp/future-system-operator-ui-demo/context_bundle.json`
- `.tmp/future-system-operator-ui-demo/operator_runs/`

## Cleanup Behavior
- Uses existing Makefile cleanup target.
- Removes only `.tmp/future-system-operator-ui-demo`.
- Leaves `.tmp` root and non-demo files untouched.

## Boundaries Preserved
- Tooling/tests/docs only.
- No `src/polymarket_arb/*` changes.
- No runtime app behavior changes.
- No DB/queue/job/notification/scheduling/trading/execution additions.
- No committed evidence screenshot changes.

## Validation Commands and Results
Commands run:

```bash
git status -sb
git diff --stat
bash -n scripts/launch_future_system_operator_ui_demo.sh
bash -n scripts/validate_future_system_operator_ui_demo_launcher.sh
test -x scripts/validate_future_system_operator_ui_demo_launcher.sh
make -n future-system-operator-ui-demo-validate
make future-system-operator-ui-demo-validate
test ! -e .tmp/future-system-operator-ui-demo
test -d evidence/local-operator-ui
find evidence/local-operator-ui -maxdepth 1 -type f | sort
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

Results:
- `git status -sb`: expected tracked/untracked changes for this phase only.
- `git diff --stat`: Makefile/docs/current-phase tracked diffs only.
- `bash -n scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `bash -n scripts/validate_future_system_operator_ui_demo_launcher.sh`: `OK`.
- `test -x scripts/validate_future_system_operator_ui_demo_launcher.sh`: `OK`.
- `make -n future-system-operator-ui-demo-validate`: prints validation script invocation.
- `make future-system-operator-ui-demo-validate`: passed full smoke flow and printed final success message.
- `test ! -e .tmp/future-system-operator-ui-demo`: `OK`.
- `test -d evidence/local-operator-ui`: `OK`.
- `find evidence/local-operator-ui -maxdepth 1 -type f | sort`: expected evidence files present.
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `39 passed, 1 warning`.
- `ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `All checks passed!`
- `mypy src/future_system/operator_ui`: `Success: no issues found in 9 source files`.
