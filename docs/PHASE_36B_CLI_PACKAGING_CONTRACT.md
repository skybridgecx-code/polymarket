# Phase 36B — CLI Packaging Contract

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36b-cli-packaging-contract`
- Phase: `36B — CLI packaging contract`
- Source checkpoint: `main` after Phase 36A

## Purpose
This phase defines the exact CLI contract for the first operator-facing review outcome packaging entrypoint.

This phase is docs-only. It does not implement the CLI.

## Chosen entrypoint
The first operator-facing entrypoint should be a Python module CLI:

- `python -m future_system.cli.review_outcome_package`

## Required CLI arguments
Required:
- `--run-id`
- `--artifacts-root`

Optional:
- `--target-root`

## Expected invocation
Default target-root behavior should package into a deterministic local directory under the artifacts root or another bounded local target chosen in implementation.

Example shape:

```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs# Phase 36B — CLI Packaging Contract

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36b-cli-packaging-contract`
- Phase: `36B — CLI packaging contract`
- Source checkpoint: `main` after Phase 36A

## Purpose
This phase defines the exact CLI contract for the first operator-facing review outcome packaging entrypoint.

This phase is docs-only. It does not implement the CLI.

## Chosen entrypoint
The first operator-facing entrypoint should be a Python module CLI:

- `python -m future_system.cli.review_outcome_package`

## Required CLI arguments
Required:
- `--run-id`
- `--artifacts-root`

Optional:
- `--target-root`

## Expected invocation
Default target-root behavior should package into a deterministic local directory under the artifacts root or another bounded local target chosen in implementation.

Example shape:
```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs
