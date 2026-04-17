# Phase 29D — Demo Launcher Prepare-Only Mode

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-29d-demo-launcher-prepare-only-mode`
- Phase: `29D — demo launcher prepare-only mode`
- Source checkpoint: Phase 29C cleanup target baseline

## What Changed
- Updated launcher script to support `PREPARE_ONLY=1`:
  - [scripts/launch_future_system_operator_ui_demo.sh](../scripts/launch_future_system_operator_ui_demo.sh)
- Added Makefile target:
  - `future-system-operator-ui-demo-prepare`

## Prepare-Only Behavior
When `PREPARE_ONLY=1`, the launcher:
- generates deterministic context bundle JSON
- generates demo review artifacts via CLI with:
  - `--analyst-mode stub`
  - `--initialize-operator-review`
- prints artifact root, run id, list URL, and detail URL
- exits with success without starting Uvicorn and without binding a port

## Exact Commands
- Make target:
  - `make future-system-operator-ui-demo-prepare`
- Direct env usage:
  - `PREPARE_ONLY=1 bash scripts/launch_future_system_operator_ui_demo.sh`
- Optional port override for printed URLs:
  - `PORT=8010 make future-system-operator-ui-demo-prepare`

## Generated Temp Paths
- `.tmp/future-system-operator-ui-demo/context_bundle.json`
- `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json`
- `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md`
- `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`

## Boundaries Preserved
- Launcher UX/Makefile/docs changes only.
- No runtime app code changes.
- No changes under `src/polymarket_arb/*`.
- No evidence screenshot or evidence file changes.
- No DB/queue/job/notification/scheduling/production-trading/execution behavior.

## Validation Commands and Results
Commands run:

```bash
git status -sb
git diff --stat
bash -n scripts/launch_future_system_operator_ui_demo.sh
test -x scripts/launch_future_system_operator_ui_demo.sh
make -n future-system-operator-ui-demo
make -n future-system-operator-ui-demo-prepare
make -n future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare
test -f .tmp/future-system-operator-ui-demo/context_bundle.json
test -f .tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json
test -f .tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md
test -f .tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json
make future-system-operator-ui-demo-clean
test ! -e .tmp/future-system-operator-ui-demo
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

Results:
- `git status -sb`: expected tracked/untracked changes for this phase only.
- `git diff --stat`: launcher/Makefile/docs/current-phase tracked diffs only.
- `bash -n scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `test -x scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `make -n future-system-operator-ui-demo`: prints launcher invocation.
- `make -n future-system-operator-ui-demo-prepare`: prints `PREPARE_ONLY=1` launcher invocation.
- `make -n future-system-operator-ui-demo-clean`: prints bounded cleanup commands for `.tmp/future-system-operator-ui-demo`.
- `make future-system-operator-ui-demo-clean`: cleanup succeeds.
- `make future-system-operator-ui-demo-prepare`: deterministic bundle/artifact/metadata files created and message confirms Uvicorn was not started.
- Artifact file assertions all passed:
  - `context_bundle.json`
  - `theme_ctx_strong.analysis_success_export.json`
  - `theme_ctx_strong.analysis_success_export.md`
  - `theme_ctx_strong.analysis_success_export.operator_review.json`
- `make future-system-operator-ui-demo-clean`: cleanup succeeds.
- `test ! -e .tmp/future-system-operator-ui-demo`: `OK`.
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `39 passed, 1 warning`.
- `ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `All checks passed!`
- `mypy src/future_system/operator_ui`: `Success: no issues found in 9 source files`.
