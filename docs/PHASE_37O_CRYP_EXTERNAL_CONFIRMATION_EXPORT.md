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

- asset source: `candidate.primary_symbol`
- signal source: `comparison.polymarket_summary.direction`
- `bullish -> buy`
- `bearish -> sell`
- `mixed` or `unknown` -> `neutral` source intent -> `veto`
- any non-`allow` policy decision -> `veto`
- confidence adjustment: bounded from `candidate.confidence_score`

The asset source is explicit and bounded. The producer accepts a `candidate.primary_symbol`
that resolves to `BTC`, `ETH`, `SOL`, or `XRP` only. Examples:

- `BTC`, `BTC-PERP`, `BTCUSD`, `BTCUSDT` -> `BTC`
- `ETH`, `ETH-PERP`, `ETHUSD`, `ETHUSDT` -> `ETH`
- `SOL`, `SOL-PERP`, `SOLUSD`, `SOLUSDT` -> `SOL`
- `XRP`, `XRP-PERP`, `XRPUSD`, `XRPUSDT` -> `XRP`

Missing or unsupported values fail explicitly. They are not inferred from prose, markdown,
market titles, or broad matched-symbol lists.

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

## Per-Asset Operator Flow

Each asset uses the same three producer steps. The only asset-specific requirement is that
the context bundle's `candidate.primary_symbol` resolves to the intended asset.

### BTC

Required context field:

```json
{"candidate": {"primary_symbol": "BTC-PERP"}}
```

Commands:

```bash
.venv/bin/python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/btc_context_bundle.json \
  --target-directory /absolute/path/operator_runs/btc \
  --analyst-mode stub \
  --initialize-operator-review

.venv/bin/python -m future_system.cli.review_outcome_package \
  --run-id <btc_run_id> \
  --artifacts-root /absolute/path/operator_runs/btc \
  --target-root /absolute/path/packages

.venv/bin/python -m future_system.cli.cryp_external_confirmation_export \
  --package-dir /absolute/path/packages/<btc_run_id>.package \
  --output-path /absolute/path/exports/btc_external_confirmation.json
```

Output asset: `BTCUSD`.

### ETH

Required context field:

```json
{"candidate": {"primary_symbol": "ETH-PERP"}}
```

Commands:

```bash
.venv/bin/python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/eth_context_bundle.json \
  --target-directory /absolute/path/operator_runs/eth \
  --analyst-mode stub \
  --initialize-operator-review

.venv/bin/python -m future_system.cli.review_outcome_package \
  --run-id <eth_run_id> \
  --artifacts-root /absolute/path/operator_runs/eth \
  --target-root /absolute/path/packages

.venv/bin/python -m future_system.cli.cryp_external_confirmation_export \
  --package-dir /absolute/path/packages/<eth_run_id>.package \
  --output-path /absolute/path/exports/eth_external_confirmation.json
```

Output asset: `ETHUSD`.

### SOL

Required context field:

```json
{"candidate": {"primary_symbol": "SOL-PERP"}}
```

Commands:

```bash
.venv/bin/python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/sol_context_bundle.json \
  --target-directory /absolute/path/operator_runs/sol \
  --analyst-mode stub \
  --initialize-operator-review

.venv/bin/python -m future_system.cli.review_outcome_package \
  --run-id <sol_run_id> \
  --artifacts-root /absolute/path/operator_runs/sol \
  --target-root /absolute/path/packages

.venv/bin/python -m future_system.cli.cryp_external_confirmation_export \
  --package-dir /absolute/path/packages/<sol_run_id>.package \
  --output-path /absolute/path/exports/sol_external_confirmation.json
```

Output asset: `SOLUSD`.

### XRP

Required context field:

```json
{"candidate": {"primary_symbol": "XRP-PERP"}}
```

Commands:

```bash
.venv/bin/python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/xrp_context_bundle.json \
  --target-directory /absolute/path/operator_runs/xrp \
  --analyst-mode stub \
  --initialize-operator-review

.venv/bin/python -m future_system.cli.review_outcome_package \
  --run-id <xrp_run_id> \
  --artifacts-root /absolute/path/operator_runs/xrp \
  --target-root /absolute/path/packages

.venv/bin/python -m future_system.cli.cryp_external_confirmation_export \
  --package-dir /absolute/path/packages/<xrp_run_id>.package \
  --output-path /absolute/path/exports/xrp_external_confirmation.json
```

Output asset: `XRPUSD`.

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
.venv/bin/ruff check src/future_system/cryp_external_confirmation_signal.py src/future_system/review_exports/builder.py src/future_system/execution_boundary_contract/cryp_confirmation_export.py src/future_system/cli/cryp_external_confirmation_export.py tests/future_system/test_cryp_external_confirmation_export.py
```
