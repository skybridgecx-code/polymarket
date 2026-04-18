# Phase 34D — Demo Workflow End-to-End Smoke Checklist

## Scope
Docs-only checklist for the full local `future_system` operator UI demo workflow:
- validate
- prepare
- launch
- list page
- detail page
- local decision update
- cleanup

## Expected Demo Constants
- Expected run id: `theme_ctx_strong.analysis_success_export`
- Expected temp paths:
  - `.tmp/future-system-operator-ui-demo/context_bundle.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/`
- Expected URLs:
  - `http://127.0.0.1:8000`
  - `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`

## Command Sequence (Exact)
```bash
make future-system-operator-ui-demo-validate
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare
make future-system-operator-ui-demo
PORT=8010 make future-system-operator-ui-demo
make future-system-operator-ui-demo-clean
```

## End-to-End Checklist

### 1) Validation Step
- Run: `make future-system-operator-ui-demo-validate`
- Confirm validation target passes with final success message.

### 2) Prepare-Only Step
- Run: `make future-system-operator-ui-demo-clean`
- Run: `make future-system-operator-ui-demo-prepare`
- Confirm expected files exist:
  - `.tmp/future-system-operator-ui-demo/context_bundle.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json`
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md`
- Confirm operator review companion metadata exists:
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`

### 3) Launch Step
- Default launch command: `make future-system-operator-ui-demo`
- If `8000` is busy, use alternate port: `PORT=8010 make future-system-operator-ui-demo`
- Confirm launcher prints list/detail URLs and selected port.

### 4) List Page Check
- Open: `http://127.0.0.1:8000`
- Confirm:
  - `Local Review Runs` title is visible.
  - artifact root/configured directory status is understandable.
  - create form guidance is understandable.
  - empty/list state guidance is understandable.

### 5) Detail Page Check
- Open: `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`
- Confirm:
  - run context is understandable.
  - artifact path semantics are understandable.
  - operator review metadata state is understandable.
  - update form local-save guidance is understandable.

### 6) Local Decision Update Step
- In detail page, apply a small update:
  - set `review_status`
  - optionally set decision/notes/reviewer
- Submit: `Save Local Decision`
- Confirm saved result renders on page.
- Confirm write scope is local companion metadata only (`X.operator_review.json`).

### 7) Cleanup Step
- Run: `make future-system-operator-ui-demo-clean`
- Confirm demo temp directory removal:
  - `.tmp/future-system-operator-ui-demo` no longer exists.

### 8) Failure Handling
- Missing `python-multipart`:
  - install with `.venv/bin/python -m pip install python-multipart`
  - rerun launcher
- Port already in use:
  - run `PORT=8010 make future-system-operator-ui-demo`
- Interrupted run cleanup:
  - run `make future-system-operator-ui-demo-clean`
  - confirm demo temp directory is removed
- During this smoke phase:
  - do not change runtime code

## Boundaries
- Docs-only phase checklist.
- No runtime behavior changes.
- No test changes.
- No evidence screenshot changes.
- No `src/polymarket_arb/*` changes.
