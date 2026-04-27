# Phase 32D — List/Create UX Manual Smoke

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-32d-list-create-ux-manual-smoke`
- Phase: `32D — list/create UX manual smoke`
- Source checkpoint: `32C — list/create template UX polish`

## Purpose
Provide a repeatable manual smoke checklist for verifying Phase 32C list/create UX polish using existing local demo launcher tooling.

This phase is docs-only and does not change runtime behavior, tests, or evidence screenshots.

## Setup Commands
Run from repo root:

```bash
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare
make future-system-operator-ui-demo
```

Port conflict fallback:

```bash
PORT=8010 make future-system-operator-ui-demo
```

## URL To Verify
- List page: `http://127.0.0.1:8000`

## List/Create UX Manual Checklist
- [ ] `Local Review Runs` title is visible.
- [ ] Local artifact-file workflow intro copy is understandable.
- [ ] Artifact root/configured directory status is understandable.
- [ ] `Create Local Review Run` section is visible.
- [ ] `Context Source JSON Path` guidance is understandable.
- [ ] `Target Subdirectory` guidance is understandable.
- [ ] `Analyst Mode` guidance is understandable.
- [ ] `Run Analysis` expectations are clear.
- [ ] No-runs/empty-state guidance is understandable.
- [ ] Trigger error recovery guidance is understandable and still uses `role="alert"`.

## Expected Validation Commands
```bash
make future-system-operator-ui-demo-validate
pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py
mypy src/future_system/operator_ui
```

## Failure Handling
- Port already in use: run with `PORT=8010 make future-system-operator-ui-demo`.
- Cleanup generated temp data: `make future-system-operator-ui-demo-clean`.
- During this manual-smoke phase, do not change runtime code; record findings for a later explicit implementation phase.

## Boundaries
- Docs-only phase.
- No runtime app behavior changes.
- No test changes.
- No screenshot or committed evidence-file changes.
- No DB/queue/jobs/notifications/scheduling/trading/execution scope.
