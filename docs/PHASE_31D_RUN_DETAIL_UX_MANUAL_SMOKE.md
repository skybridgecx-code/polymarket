# Phase 31D — Run Detail UX Manual Smoke

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-31d-run-detail-ux-manual-smoke`
- Phase: `31D — run detail UX manual smoke`
- Source checkpoint: `31C — run detail template UX polish`

## Purpose
Provide a repeatable manual smoke checklist for verifying the Phase 31C run detail UX polish using existing local launcher tooling.

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

## URLs To Verify
Default port (`8000`):
- List page: `http://127.0.0.1:8000`
- Detail page: `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`

Alternate port (`8010`):
- List page: `http://127.0.0.1:8010`
- Detail page: `http://127.0.0.1:8010/runs/theme_ctx_strong.analysis_success_export`

## Run Detail UX Manual Checklist
- [ ] Top run context is clear at the top of detail page.
- [ ] Run id is visible and easy to identify.
- [ ] Status and review metadata state are understandable at a glance.
- [ ] Artifact path section clearly explains markdown/json/decision metadata paths.
- [ ] Empty metadata guidance is understandable when viewing a run without initialized companion metadata.
- [ ] Update form copy clearly states save behavior is local companion metadata write only.
- [ ] `Save Local Decision` remains visible when companion metadata exists.
- [ ] `Back to local review runs` link is preserved.

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
