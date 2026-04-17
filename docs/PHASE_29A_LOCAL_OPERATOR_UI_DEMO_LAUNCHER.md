# Phase 29A — Local Operator UI Demo Launcher

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-29a-local-operator-ui-demo-launcher`
- Phase: `29A — local operator UI demo launcher`
- Source checkpoint: Phase 28A release index/handoff

## What Was Added
- Added local launcher script: [scripts/launch_future_system_operator_ui_demo.sh](../scripts/launch_future_system_operator_ui_demo.sh)
- Added Makefile convenience target:
  - `future-system-operator-ui-demo:`
  - `bash scripts/launch_future_system_operator_ui_demo.sh`
- Updated release index with launcher references:
  - [FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md](./FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md)
- Updated current phase pointer:
  - `.codex/phases/current_phase.md`

## Exact Launch Command
- Script command: `bash scripts/launch_future_system_operator_ui_demo.sh`
- Make command: `make future-system-operator-ui-demo`

## Deterministic Temp Paths
- Demo root: `.tmp/future-system-operator-ui-demo/`
- Generated context bundle: `.tmp/future-system-operator-ui-demo/context_bundle.json`
- Generated artifact root: `.tmp/future-system-operator-ui-demo/operator_runs/`

## Expected URLs
- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`

## Launcher Behavior
- Requires execution from repo root.
- Prefers `.venv/bin/python`; falls back to `python3`.
- Verifies `python-multipart` is installed before launch.
- Fails with explicit install guidance if missing:
  - `.venv/bin/python -m pip install python-multipart`
- Builds deterministic `OpportunityContextBundle` JSON from fixture input:
  - `tests/fixtures/future_system/context_bundle/context_bundle_inputs.json`
  - case: `strong_complete`
- Runs:
  - `python -m future_system.cli.review_artifacts`
  - `--analyst-mode stub`
  - `--initialize-operator-review`
- Exports `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` to generated `operator_runs` path.
- Launches:
  - `python -m uvicorn future_system.operator_ui.app_entry:create_operator_ui_app --factory --reload`

## Boundaries Preserved
- No changes under `src/polymarket_arb/*`.
- No DB, queue, job, scheduler, notification, inbox, production-trading, or execution behavior added.
- No runtime behavior changes to shipped `future_system` codepaths.
- No test changes.
- No evidence screenshot changes.
- Writes are scoped to `.tmp/future-system-operator-ui-demo/` (outside normal runtime behavior).

## Validation Commands and Results
Commands run:

```bash
git status -sb
git diff --stat
bash -n scripts/launch_future_system_operator_ui_demo.sh
test -x scripts/launch_future_system_operator_ui_demo.sh
make -n future-system-operator-ui-demo
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

Results:
- `git status -sb`: expected tracked/untracked changes for this phase only.
- `git diff --stat`: expected docs/Makefile/current-phase tracked diffs only.
- `bash -n scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `test -x scripts/launch_future_system_operator_ui_demo.sh`: `OK`.
- `make -n future-system-operator-ui-demo`: prints `bash scripts/launch_future_system_operator_ui_demo.sh`.
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `39 passed, 1 warning`.
- `ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `All checks passed!`
- `mypy src/future_system/operator_ui`: `Success: no issues found in 9 source files`.

Optional runtime smoke:
- Launcher executed artifact prep and printed expected URLs.
- Uvicorn startup failed with `[Errno 48] Address already in use` on `127.0.0.1:8000` in local environment.
- No background server was left running by this phase.

## Exit Criteria
- Launcher script exists and is executable.
- Make target exists and points to launcher script.
- Release index references launcher.
- Current phase pointer updated to 29A.
- Validation command set executed.
