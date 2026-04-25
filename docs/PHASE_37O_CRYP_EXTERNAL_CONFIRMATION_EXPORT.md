# Phase 37O — cryp External Confirmation Export

## What Matters

This phase adds a producer-side bridge from a reviewed Polymarket package into the exact
`cryp` external confirmation advisory artifact consumed by:

```bash
--external-confirmation-path <json>
```

The exported JSON uses the existing `cryp` schema:

- `artifact_kind`
- `asset`
- `directional_bias`
- `confidence_adjustment`
- `rationale`
- `source_system`
- `supporting_tags`
- `veto_trade`
- `correlation_id`
- `observed_at_epoch_ns`

No `cryp` runtime, execution, strategy, or live-trading code is changed by this phase.

## Source Contract

The exporter reads an already-reviewed package directory containing `handoff_payload.json`.
The referenced JSON review artifact and generated handoff payload must contain one
reviewed signal block:

```json
{
  "cryp_external_confirmation_signal": {
    "asset": "BTC",
    "signal": "buy",
    "confidence_adjustment": 0.12,
    "rationale": "Reviewed Polymarket outcome supports the crypto advisory.",
    "source_system": "polymarket-arb",
    "supporting_tags": ["polymarket", "reviewed", "bridge_export"],
    "observed_at_epoch_ns": 1700000000000000002
  }
}
```

The upstream producer step that creates this block is the review artifact generation step.
Run it from `/Users/muhammadaatif/polymarket-arb` against an `OpportunityContextBundle`
that carries structured asset and Polymarket direction fields:

```bash
.venv/bin/python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/context_bundle.json \
  --target-directory /absolute/path/operator_runs \
  --analyst-mode stub \
  --initialize-operator-review
```

The signal block is derived only from structured fields, not markdown prose:

- asset source: `candidate.primary_symbol`, falling back to structured crypto asset links
- signal source: `comparison.polymarket_summary.direction`
- `bullish -> buy`
- `bearish -> sell`
- `mixed` or `unknown` -> `veto`
- any non-`allow` policy decision -> `veto`
- confidence adjustment: bounded from `candidate.confidence_score`

After operator approval, package the same reviewed run:

```bash
.venv/bin/python -m future_system.cli.review_outcome_package \
  --run-id <run_id> \
  --artifacts-root /absolute/path/operator_runs \
  --target-root /absolute/path/packages
```

`review_outcome_package` validates and preserves the reviewed signal into
`handoff_payload.json`; no manual JSON editing is required. Existing artifacts produced
before this producer wiring need to be regenerated or they will still be missing the
structured signal block.

The package must be:

- `run_status=success`
- `review_status=decided`
- `operator_decision=approve`

This keeps the bridge on reviewed and packaged output only. It does not scrape live
Polymarket data and does not infer trade advice from markdown prose.

## Bounded Asset Mapping

Only these assets are supported in this phase:

- `BTC -> BTCUSD`
- `ETH -> ETHUSD`
- `SOL -> SOLUSD`
- `XRP -> XRPUSD`

Unsupported assets fail explicitly.

## Signal Mapping

- `buy -> directional_bias=buy, veto_trade=false`
- `sell -> directional_bias=sell, veto_trade=false`
- `veto -> directional_bias=neutral, veto_trade=true`

## Export Command

Run from `/Users/muhammadaatif/polymarket-arb`:

```bash
.venv/bin/python -m future_system.cli.cryp_external_confirmation_export \
  --package-dir /absolute/path/theme_btc_regulation.analysis_success_export.package \
  --output-path /absolute/path/btc_external_confirmation.json
```

## cryp Consumption Command

Run from `/Users/muhammadaatif/cryp`:

```bash
.venv/bin/python -m crypto_agent.cli.forward_paper tests/fixtures/paper_candles_breakout_long.jsonl \
  --runtime-id polymarket-btc-advisory-forward-paper \
  --execution-mode paper \
  --external-confirmation-path /absolute/path/btc_external_confirmation.json
```

## Non-Goals

- no crypto execution changes
- no advisory-strengthening logic
- no broad cross-repo refactor
- no live trading changes
- no new external transport
- no raw live Polymarket scraping

## Validation

```bash
.venv/bin/pytest -q tests/future_system/test_cryp_external_confirmation_export.py
.venv/bin/pytest -q tests/future_system/test_review_cli_review_artifacts.py tests/future_system/test_operator_review_outcome_packaging.py
.venv/bin/ruff check src/future_system/execution_boundary_contract/cryp_confirmation_export.py src/future_system/cli/cryp_external_confirmation_export.py tests/future_system/test_cryp_external_confirmation_export.py
```
