# Phase 35E — Review Outcome Packaging Manual Smoke

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-35e-review-outcome-packaging-manual-smoke`
- Phase: `35E — review outcome packaging manual smoke`
- Source checkpoint: `phase-35d-review-outcome-packaging-implementation`

## Purpose
This phase defines a repeatable manual smoke path for the first bounded local review outcome packaging flow.

This phase does not change runtime behavior. It verifies that a reviewed run can be packaged into deterministic local handoff artifacts.

## Expected package shape
For a reviewed run id like:

- `theme_ctx_strong.analysis_success_export`

the packaging flow should create:

- `<target_root>/<run_id>.package/`
  - `handoff_summary.md`
  - `handoff_payload.json`

## Manual smoke setup
Use a temporary local smoke directory:

- `.tmp/review-outcome-packaging-smoke/`

## Manual smoke steps

### 1. Clean prior smoke output
```bash
rm -rf .tmp/review-outcome-packaging-smoke
mkdir -p .tmp/review-outcome-packaging-smoke
