# Phase 36B — CLI Packaging Contract

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36b-cli-packaging-contract`
- Phase: `36B — CLI packaging contract`
- Source checkpoint: `main` after Phase 36A

## Purpose
Define the operator-facing contract for the first local review outcome packaging entrypoint.

This phase is docs-only and does not implement runtime behavior.

## Chosen Entrypoint
The first packaging entrypoint is a Python module CLI:

- `python -m future_system.cli.review_outcome_package`

## Required Arguments
Required:
- `--run-id`
- `--artifacts-root`

Optional:
- `--target-root`

## Invocation Shape
Canonical command:

```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
```

Default behavior when `--target-root` is omitted:
- package output is written under `artifacts_root`

## Inputs Resolved By CLI
For `run_id = X`, the CLI resolves these files from `artifacts_root`:
- `X.md`
- `X.json`
- `X.operator_review.json`

## Output Contract
Package directory:
- `<target_root>/<run_id>.package/`

Package files:
- `handoff_summary.md`
- `handoff_payload.json`

Success stdout must include:
- `run_id: ...`
- `package_dir: ...`
- `handoff_summary_path: ...`
- `handoff_payload_path: ...`

## Failure Contract
On operator-facing validation failure, CLI:
- writes `review_outcome_package_cli_error: ...` to stderr
- returns non-zero exit code (`2`)

Expected failure classes:
- missing markdown/json artifact file
- missing operator review metadata file
- invalid operator review metadata shape
- run id mismatch between `--run-id` and metadata artifact block
- invalid target root/path semantics

## Boundaries
- local artifact-file workflow only
- no UI behavior change requirement
- no remote delivery
- no DB/queue/scheduling/notification/inbox/background-job behavior
- no `src/polymarket_arb/*` changes
- no production trading or execution behavior
