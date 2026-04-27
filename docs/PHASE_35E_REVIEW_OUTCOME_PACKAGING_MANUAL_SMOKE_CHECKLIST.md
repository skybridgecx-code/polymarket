# Phase 35E — Review Outcome Packaging Manual Smoke Checklist

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-35e-review-outcome-packaging-manual-smoke`
- Phase: `35E — review outcome packaging manual smoke`
- Reconciled in: `36E — CLI packaging track closeout`

## Purpose
Provide a repeatable local checklist for packaging one reviewed run into deterministic handoff artifacts.

This checklist is documentation-only and does not change runtime behavior.

## Preconditions
- local run artifacts exist for one run id
- companion operator review metadata exists for the same run id

Reference run id used in demo flow:
- `theme_ctx_strong.analysis_success_export`

## Checklist

### 1. Prepare deterministic local artifacts
```bash
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare
```

### 2. Complete local decision update before packaging
- launch UI with `make future-system-operator-ui-demo`
- open detail page for `theme_ctx_strong.analysis_success_export`
- save decision metadata using `Save Local Decision`

### 3. Run packaging CLI
```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
```

### 4. Verify package outputs
Expected package directory:
- `.tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package/`

Expected files:
- `handoff_summary.md`
- `handoff_payload.json`

### 5. Cleanup
```bash
make future-system-operator-ui-demo-clean
```

## Failure Notes
- If metadata is missing or invalid, CLI emits:
  - `review_outcome_package_cli_error: ...`
- If UI launch fails due missing multipart dependency:
  - `.venv/bin/python -m pip install python-multipart`

## Boundaries
- local artifact-file workflow only
- no remote delivery
- no DB/queue/scheduling/notification/background-job behavior
- no production trading or execution behavior
