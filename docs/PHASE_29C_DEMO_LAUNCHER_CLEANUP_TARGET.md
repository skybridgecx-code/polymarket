# Phase 29C — Demo Launcher Cleanup Target

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-29c-demo-launcher-cleanup-target`
- Phase: `29C — demo launcher cleanup target`
- Source checkpoint: Phase 29B launcher port-handling baseline

## What Was Added
- Added Makefile cleanup target:
  - `future-system-operator-ui-demo-clean`

## Exact Command
- `make future-system-operator-ui-demo-clean`

## What It Removes
- `.tmp/future-system-operator-ui-demo`

## What It Does Not Remove
- `.tmp` as a whole
- `evidence/`
- `docs/`
- `src/`
- committed evidence screenshots under `evidence/local-operator-ui/`

## Target Behavior
- Prints clear cleanup messages.
- Uses safe `rm -rf` on one bounded path only.
- Succeeds even when `.tmp/future-system-operator-ui-demo` does not exist.

## Boundaries Preserved
- Makefile/docs-only change.
- No runtime app behavior changes.
- No changes under `src/polymarket_arb/*`.
- No changes to evidence screenshots or evidence content.
- No DB/queue/job/notification/scheduling/production-trading/execution behavior.

## Validation Commands and Results
Commands run:

```bash
git status -sb
git diff --stat
make -n future-system-operator-ui-demo
make -n future-system-operator-ui-demo-clean
mkdir -p .tmp/future-system-operator-ui-demo/operator_runs
make future-system-operator-ui-demo-clean
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
- `make -n future-system-operator-ui-demo`: prints `bash scripts/launch_future_system_operator_ui_demo.sh`.
- `make -n future-system-operator-ui-demo-clean`: prints the bounded cleanup commands for `.tmp/future-system-operator-ui-demo`.
- `mkdir -p .tmp/future-system-operator-ui-demo/operator_runs`: demo path created successfully.
- `make future-system-operator-ui-demo-clean`: printed cleanup message and removed only `.tmp/future-system-operator-ui-demo`.
- `test ! -e .tmp/future-system-operator-ui-demo`: `OK`.
- `test -d evidence/local-operator-ui`: `OK`.
- `find evidence/local-operator-ui -maxdepth 1 -type f | sort`: all expected evidence files present.
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `39 passed, 1 warning`.
- `ruff check src/future_system/operator_ui src/future_system/cli tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`: `All checks passed!`
- `mypy src/future_system/operator_ui`: `Success: no issues found in 9 source files`.
