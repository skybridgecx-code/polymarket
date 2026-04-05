# Operator Runbook

## Scope

This runbook documents the already-shipped read-only operator surface.

It covers:

- `orchestrate-refresh`
- `paper-trade`
- `review-packet`
- `replay-evaluate`
- checkpoint inspection
- `/health` interpretation

It does not add or imply:

- live trading
- auth
- private keys
- new routes
- new CLI commands
- scoring changes

## Runtime And Environment Expectations

Current runtime behavior is grounded in `src/polymarket_arb/config.py`.

The CLI and API load settings from:

- `.env` when present
- process environment variables

Current relevant environment variables and defaults:

- `POLY_GAMMA_BASE_URL`: `https://gamma-api.polymarket.com`
- `POLY_CLOB_BASE_URL`: `https://clob.polymarket.com`
- `POLY_DATA_BASE_URL`: `https://data-api.polymarket.com`
- `POLY_WS_MARKET_URL`: `wss://ws-subscriptions-clob.polymarket.com/ws/market`
- `DATA_DIR`: `./data`
- `STATE_DIR`: `./state`
- `LOG_LEVEL`: `INFO`

Current orchestration timing defaults:

- `scan_stale_after_seconds = 300`
- `relationship_stale_after_seconds = 300`
- `websocket_stale_after_seconds = 120`
- `websocket_receive_timeout_seconds = 2.0`
- `websocket_reconnect_attempts = 2`

Current checkpoint filename:

- `runtime_orchestrator_checkpoint.json`

Current paper-trade operator-relevant defaults:

- `paper_trade_min_size = 5`
- `paper_trade_max_size = 10`
- `paper_trade_max_capacity_utilization = 0.5`
- `paper_trade_min_simulated_edge_cents = 5`
- `paper_trade_base_slippage_bps = 10`
- `paper_trade_additional_leg_slippage_bps = 5`
- `paper_trade_utilization_slippage_bps = 20`
- `paper_trade_policy_max_slippage_bps = 24`
- `paper_trade_circuit_breaker_active = false`
- `paper_trade_circuit_breaker_reason = null`

Both `DATA_DIR` and `STATE_DIR` are created automatically by settings initialization.

## Setup

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
make validate
```

## Command Runbook

### `orchestrate-refresh`

Purpose:

- run one bounded refresh cycle
- rebuild opportunities
- rebuild relationship reports
- derive websocket subscriptions from current opportunity legs
- consume only the requested number of websocket messages
- write the current checkpoint

Command:

```bash
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
```

What to inspect:

- `scan_limit`
- `relationship_limit`
- `max_websocket_messages`
- `consumed_asset_ids`
- `checkpoint`
- `health`
- `opportunities_count`
- `relationships_count`

### `paper-trade`

Purpose:

- transform opportunity rows into execution plans
- simulate fills using the existing simulator
- attach post-simulation `policy_decision`

Command:

```bash
python -m polymarket_arb.cli paper-trade --limit 5
```

Deterministic fixture mode:

```bash
python -m polymarket_arb.cli paper-trade --limit 5 --fixture-path tests/fixtures/scenarios/phase7b_paper_trade.json
```

What to inspect on each row:

- `status`
- `rejection_reason`
- `explanation`
- `risk_flags`
- `simulated_result`
- `policy_decision`

`policy_decision` is applied after simulation. It does not replace planner rejection or simulator rejection behavior.

### `review-packet`

Purpose:

- export deterministic packet JSON for `opportunities`, `relationships`, or `paper_trade`

Commands:

```bash
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli review-packet --packet-type relationships --limit 10
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10
```

Deterministic fixture mode:

```bash
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json
```

What to inspect:

- `packet_id`
- `packet_type`
- `created_at`
- `source_references`
- `summarized_findings`
- `status`
- `notes`

### `replay-evaluate`

Purpose:

- compare two review packet files
- report explicit drift and match counts

Command:

```bash
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
```

What to inspect:

- `evaluation_id`
- `subject_type`
- `compared_records_count`
- `matches_count`
- `mismatches_count`
- `drift_reasons`
- `status`
- `explanation`

## Checkpoint Inspection Workflow

Default checkpoint path:

- `state/runtime_orchestrator_checkpoint.json`

Recommended bounded inspection flow:

1. Run one bounded refresh.
2. Inspect the checkpoint JSON directly.
3. Interpret `/health` or the embedded `health` payload from the refresh output.
4. If `stale_reasons` or `last_error` are present, inspect those before rerunning.

Exact commands:

```bash
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1 > /tmp/orchestrate-refresh.json
python -m json.tool state/runtime_orchestrator_checkpoint.json
python -m json.tool /tmp/orchestrate-refresh.json
```

Checkpoint fields to inspect first:

- `checkpoint_written_at`
- `last_scan_refresh_at`
- `last_relationship_refresh_at`
- `last_websocket_connect_at`
- `last_websocket_event_at`
- `websocket_reconnect_count`
- `websocket_disconnect_count`
- `subscribed_asset_ids`
- `last_refresh_limit`
- `last_relationship_limit`
- `last_error`
- `stale_reasons`

Interpretation guidance:

- if `subscribed_asset_ids` is empty, websocket freshness is not evaluated
- if `subscribed_asset_ids` is populated, websocket freshness depends on `last_websocket_event_at`
- if `last_error` is non-null, health will include `last_error_present`
- the checkpoint is operational state only, not historical storage

## Health Interpretation

The health model is derived from checkpoint content in `OrchestrationHealthStatus.from_checkpoint()` and `RefreshOrchestratorService._stale_reasons()`.

Current health statuses:

- `idle`
- `ok`
- `stale`

Current meanings:

- `idle`: both `last_scan_refresh_at` and `last_relationship_refresh_at` are still `null`
- `ok`: at least one refresh has run and there are no current stale reasons
- `stale`: at least one refresh has run and `stale_reasons` is non-empty

Important current behavior:

- `status` and `stale` are not identical fields
- an untouched system can report `status = "idle"` and still return `stale = true` with never-refreshed reasons

Current stale reasons and meanings:

- `scan_never_refreshed`: no scan refresh has been written yet
- `scan_refresh_overdue`: `last_scan_refresh_at` is older than `scan_stale_after_seconds`
- `relationships_never_refreshed`: no relationship refresh has been written yet
- `relationship_refresh_overdue`: `last_relationship_refresh_at` is older than `relationship_stale_after_seconds`
- `websocket_never_received_event`: there are subscribed asset ids but no websocket event has been recorded yet
- `websocket_event_overdue`: `last_websocket_event_at` is older than `websocket_stale_after_seconds`
- `last_error_present`: `last_error` is non-null in the checkpoint

Optional local API check:

```bash
python -m uvicorn polymarket_arb.api.main:app --reload
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

## Bounded Review Workflow

The shipped review workflow is intentionally small:

1. generate a baseline packet
2. generate a candidate packet
3. run replay evaluation
4. inspect explicit drift reasons before making any judgment

Exact bounded example:

```bash
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json > /tmp/review-baseline.json
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_candidate.json > /tmp/review-candidate.json
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/review-baseline.json --candidate-path /tmp/review-candidate.json
```

Operator expectations:

- do not treat replay as an automated execution gate
- treat `mismatches_count`, `drift_reasons`, and `status` as audit inputs for manual review
- preserve rejected or weak rows in packets instead of filtering them away during review

## Phase Boundary

This runbook documents the system as shipped through Phase 10A operator hardening.

It does not introduce:

- new routes
- new CLI commands
- Python behavior changes
- policy changes
- live trading behavior
