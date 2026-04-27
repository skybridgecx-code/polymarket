# Phase 29B — Demo Launcher Port Handling

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-29b-demo-launcher-port-handling`
- Phase: `29B — demo launcher port handling`
- Source checkpoint: Phase 29A launcher baseline

## What Changed
- Updated launcher script:
  - [scripts/launch_future_system_operator_ui_demo.sh](../scripts/launch_future_system_operator_ui_demo.sh)
- Added `PORT` environment override with default `8000`.
- Added preflight port availability check before Uvicorn startup.
- Added clear startup printout for:
  - artifact root
  - run id
  - selected port
  - list URL
  - detail URL
- Kept existing deterministic demo artifact generation and `python-multipart` verification behavior.

## How To Run
- Default port:
  - `make future-system-operator-ui-demo`
- Alternate port:
  - `PORT=8001 make future-system-operator-ui-demo`
- Cleanup generated demo artifacts:
  - `make future-system-operator-ui-demo-clean`

## Expected URLs
- Default port:
  - `http://127.0.0.1:8000`
  - `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`
- Alternate port example (`PORT=8001`):
  - `http://127.0.0.1:8001`
  - `http://127.0.0.1:8001/runs/theme_ctx_strong.analysis_success_export`

## Port Conflict Behavior
- If selected port is already occupied, launcher exits before Uvicorn and prints:
  - `Port $PORT is already in use.`
  - `Try: PORT=8001 make future-system-operator-ui-demo`

## Boundaries Preserved
- Launcher UX/docs only.
- No runtime app code changes under `src/future_system/*` or `src/polymarket_arb/*`.
- No test changes.
- No evidence screenshot changes.
- No DB/queue/job/notification/scheduling/production-trading/execution behavior.
- Demo artifacts remain under `.tmp/future-system-operator-ui-demo/`.

## Validation Commands and Results
Commands run:

```bash
git status -sb
git diff --stat
bash -n scripts/launch_future_system_operator_ui_demo.sh
test -x scripts/launch_future_system_operator_ui_demo.sh
make -n future-system-operator-ui-demo
PORT=8001 make -n future-system-operator-ui-demo
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

Results:
- `git status -sb`: expected tracked/untracked changes for this phase only.
- `git diff --stat`: launcher/docs/current-phase tracked diffs only.
- `bash -n scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `test -x scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `make -n future-system-operator-ui-demo`: prints `bash scripts/launch_future_system_operator_ui_demo.sh`.
- `PORT=8001 make -n future-system-operator-ui-demo`: prints `bash scripts/launch_future_system_operator_ui_demo.sh`.
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `39 passed, 1 warning`.
- `ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `All checks passed!`
- `mypy src/future_system/operator_ui`: `Success: no issues found in 9 source files`.

Optional runtime smoke:
- Attempted launcher run with `PORT=8001`.
- Preflight conflict behavior worked as designed in this local environment:
  - `Port 8001 is already in use.`
  - `Try: PORT=8001 make future-system-operator-ui-demo`
- Uvicorn did not start, and no background server process was left running.
