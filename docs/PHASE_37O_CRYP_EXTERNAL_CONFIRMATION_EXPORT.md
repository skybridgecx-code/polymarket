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
The referenced JSON review artifact must contain one reviewed signal block:

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
.venv/bin/ruff check src/future_system/execution_boundary_contract/cryp_confirmation_export.py src/future_system/cli/cryp_external_confirmation_export.py tests/future_system/test_cryp_external_confirmation_export.py
```
