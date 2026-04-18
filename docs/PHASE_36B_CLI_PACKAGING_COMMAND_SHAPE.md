# Phase 36B — CLI Packaging Command Shape

## Proposed module
- `future_system.cli.review_outcome_package`

## Proposed arguments
### Required
- `--run-id`
  - reviewed run identifier to package
- `--artifacts-root`
  - directory containing the reviewed run artifacts and companion metadata

### Optional
- `--target-root`
  - explicit local package output root
  - if omitted, implementation may choose a bounded default under local temp/artifact roots

## Proposed path resolution
For run id:
- `theme_ctx_strong.analysis_success_export`

The CLI should look for:
- `<artifacts_root>/<run_id>.md`
- `<artifacts_root>/<run_id>.json`
- `<artifacts_root>/<run_id>.operator_review.json`

It should produce:
- `<target_root>/<run_id>.package/`
  - `handoff_summary.md`
  - `handoff_payload.json`

## Proposed success output
Success output should be concise and operator-readable, for example:
- run id
- package directory
- handoff summary path
- handoff payload path

## Proposed failure output
Failure output should:
- say what failed
- mention the run id if available
- mention the missing/invalid path when relevant
- avoid stack traces in the normal operator-facing path

## Safe first implementation rules
- local-only file writes
- deterministic filenames
- single-run only
- no hidden side effects
- no remote actions

## Candidate examples
### Example 1
```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs
