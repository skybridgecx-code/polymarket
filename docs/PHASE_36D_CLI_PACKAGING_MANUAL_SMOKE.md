# Phase 36D — CLI Packaging Manual Smoke

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36d-cli-packaging-manual-smoke`
- Phase: `36D — CLI packaging manual smoke and repo-status reconciliation`
- Source checkpoint: `phase-36c-cli-packaging-implementation`

## Purpose
Define and verify the operator manual smoke path for the shipped packaging CLI entrypoint added in 36C, and make the end-to-end local workflow explicit:

- validate
- prepare
- launch/review
- save local decision
- package
- cleanup

This phase is docs/manual-verification only. No runtime behavior changes.

## Verified CLI Entrypoint (From Code)
Implementation source:
- `src/future_system/cli/review_outcome_package.py`

Test contract source:
- `tests/future_system/test_review_outcome_package_cli.py`

Entrypoint:
```bash
python -m future_system.cli.review_outcome_package
```

Arguments:
- required: `--run-id`
- required: `--artifacts-root`
- optional: `--target-root` (defaults to `artifacts_root`)

Success output lines:
- `run_id: ...`
- `package_dir: ...`
- `handoff_summary_path: ...`
- `handoff_payload_path: ...`

Failure behavior:
- prints `review_outcome_package_cli_error: ...` to stderr
- exits non-zero (`2`)

## End-to-End Manual Smoke Path

### 1) Validate
```bash
make validate
```

### 2) Prepare deterministic local artifacts
```bash
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare
```

Expected run id:
- `theme_ctx_strong.analysis_success_export`

Expected artifacts root:
- `.tmp/future-system-operator-ui-demo/operator_runs/`

### 3) Launch UI and review
Default:
```bash
make future-system-operator-ui-demo
```

If port `8000` is busy:
```bash
PORT=8010 make future-system-operator-ui-demo
```

Open:
- list page: `http://127.0.0.1:8000`
- detail page: `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`

### 4) Save local decision in detail page
In the run detail form:
- set `review_status` (for example `decided`)
- optionally set `operator_decision`, `review_notes_summary`, `reviewer_identity`
- select `Save Local Decision`

Confirm:
- updated values render on page
- write scope remains local companion metadata only:
  - `.tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json`

### 5) Run packaging CLI
```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
```

### 6) Verify package outputs
Expected package directory:
- `.tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package/`

Expected files:
- `handoff_summary.md`
- `handoff_payload.json`

### 7) Cleanup
```bash
make future-system-operator-ui-demo-clean
```

If package target root was under demo temp root as above, cleanup also removes package output.

## Failure Handling Notes
- Missing `python-multipart` during UI launch:
  - `.venv/bin/python -m pip install python-multipart`
- Port conflict:
  - `PORT=8010 make future-system-operator-ui-demo`
- Packaging fails due missing metadata:
  - ensure run has `X.operator_review.json`
  - ensure the run id in metadata matches `--run-id`

## Boundaries Preserved
- local artifact-file workflow only
- no live execution behavior
- no auth/private-key handling
- no DB/queue/scheduler/notification/background-job behavior
- no `src/polymarket_arb/*` changes

## Validation
```bash
make validate
```
