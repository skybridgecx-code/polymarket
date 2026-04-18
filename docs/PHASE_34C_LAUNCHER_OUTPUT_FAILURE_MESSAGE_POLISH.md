# Phase 34C — Launcher Output / Failure-Message Polish

## Summary
Phase 34C polished operator-facing output in `scripts/launch_future_system_operator_ui_demo.sh` so prepare, artifact, URL, and launch states are easier to scan during local demo setup.

## What Changed
- Added stdout section headings:
  - `Prepare`
  - `Artifacts`
  - `URLs`
  - `Launch`
- Added clearer pre-launch instruction copy before Uvicorn starts.
- Added clearer `PREPARE_ONLY=1` completion copy that confirms no server start and provides the next command.
- Polished failure copy for:
  - missing fixture input file
  - context bundle generation failure from fixture input
  - missing `python-multipart`
  - port already in use
- Kept required recovery commands/messages:
  - `.venv/bin/python -m pip install python-multipart`
  - `PORT=8001 make future-system-operator-ui-demo`

## What Stayed Unchanged
- No runtime app code changes.
- No UI template changes.
- No generated path changes:
  - `.tmp/future-system-operator-ui-demo/context_bundle.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/`
- No `PORT` behavior changes (default remains `8000`, override still supported).
- No `PREPARE_ONLY` behavior changes (still prepares artifacts and exits without Uvicorn).
- No dependency auto-install behavior changes.

## Boundaries Preserved
- Tooling/docs scope only.
- No `src/polymarket_arb/*` changes.
- No DB/queue/jobs/notifications/scheduling/trading/execution behavior added.
- No evidence screenshot modifications.

## Validation Commands
```bash
git status -sb
git diff --stat
bash -n scripts/launch_future_system_operator_ui_demo.sh
bash -n scripts/validate_future_system_operator_ui_demo_launcher.sh
make future-system-operator-ui-demo-validate
PREPARE_ONLY=1 bash scripts/launch_future_system_operator_ui_demo.sh
make future-system-operator-ui-demo-clean
test ! -e .tmp/future-system-operator-ui-demo
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

## Validation Results
- All listed Phase 34C validation commands passed.
- Known non-blocking warning remains in pytest output:
  - `PendingDeprecationWarning` from `starlette.formparsers`.
