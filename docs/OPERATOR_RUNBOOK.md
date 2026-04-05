# Operator Runbook

## What This Is

This is the operator entrypoint for the shipped read-only system.

Operator read order:

1. [README.md](/Users/muhammadaatif/polymarket-arb/README.md)
2. [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)
3. [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
4. [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
5. [CODEX_HANDOFF.md](/Users/muhammadaatif/polymarket-arb/CODEX_HANDOFF.md)

This runbook covers the shipped operator surface only:

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
- policy changes

## Runtime Expectations

Current runtime behavior is grounded in [`src/polymarket_arb/config.py`](/Users/muhammadaatif/polymarket-arb/src/polymarket_arb/config.py).

Settings load from:

- `.env` when present
- process environment variables

Relevant environment variables and defaults:

- `POLY_GAMMA_BASE_URL`: `https://gamma-api.polymarket.com`
- `POLY_CLOB_BASE_URL`: `https://clob.polymarket.com`
- `POLY_DATA_BASE_URL`: `https://data-api.polymarket.com`
- `POLY_WS_MARKET_URL`: `wss://ws-subscriptions-clob.polymarket.com/ws/market`
- `DATA_DIR`: `./data`
- `STATE_DIR`: `./state`
- `LOG_LEVEL`: `INFO`

Current checkpoint file:

- `state/runtime_orchestrator_checkpoint.json`

Current orchestration timing defaults:

- `scan_stale_after_seconds = 300`
- `relationship_stale_after_seconds = 300`
- `websocket_stale_after_seconds = 120`
- `websocket_receive_timeout_seconds = 2.0`
- `websocket_reconnect_attempts = 2`

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

## Command Selection

Use `orchestrate-refresh` when you need one bounded live-data refresh, a fresh checkpoint write, or current health/staleness inspection.

Use `paper-trade` when you need current simulated execution rows with final `policy_decision` attached.

Use `review-packet` when you need a deterministic audit packet for one subject type: `opportunities`, `relationships`, or `paper_trade`.

Use `replay-evaluate` only after you already have two packet files to compare. It is packet-to-packet comparison only.

## Core Commands

Validation:

```bash
make validate
```

Bounded refresh:

```bash
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
```

Paper trade:

```bash
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli paper-trade --limit 5 --fixture-path tests/fixtures/scenarios/phase7b_paper_trade.json
```

Review packets:

```bash
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli review-packet --packet-type relationships --limit 10
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json
```

Replay evaluation:

```bash
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
```

Optional local API check:

```bash
python -m uvicorn polymarket_arb.api.main:app --reload
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

## Pre-Run Checklist

Before `orchestrate-refresh`:

- confirm the repo is in the expected branch and working tree state
- confirm `.venv` is active
- confirm `STATE_DIR` resolves to the checkpoint location you expect
- confirm you are running explicit bounded limits
- decide whether you want to preserve the current checkpoint or overwrite it with a fresh bounded run

Before `paper-trade`:

- decide whether you want live-derived rows or a deterministic fixture run
- if using fixture mode, confirm the fixture path exists
- remember that `policy_decision` is post-simulation and does not replace planner or simulator rejection logic

Before `review-packet`:

- choose the packet subject type first
- confirm the packet subject type matches the review question
- if deterministic comparison matters, prefer fixture-backed packet generation

Before `replay-evaluate`:

- confirm both packet files already exist
- confirm both packet files were generated for the same subject type
- inspect the packet JSONs before replay if their provenance is unclear

## Post-Run Checklist

After `orchestrate-refresh`:

- inspect `health.status`
- inspect `health.stale`
- inspect `health.stale_reasons`
- inspect `checkpoint.last_error`
- inspect `checkpoint.last_websocket_event_at`
- inspect `checkpoint.subscribed_asset_ids`

After checkpoint inspection:

- confirm `checkpoint_written_at` changed as expected
- confirm `last_scan_refresh_at` and `last_relationship_refresh_at` are present for a completed bounded refresh
- confirm websocket timestamps only if `subscribed_asset_ids` is non-empty
- if `last_error` is present, treat that as the first triage branch

After `paper-trade`:

- inspect row `status` before summary fields
- inspect `rejection_reason` on rejected rows
- inspect `policy_decision` on every final row
- keep rejected rows visible during review

After `review-packet`:

- confirm `packet_type`
- confirm `status`
- inspect `source_references`
- inspect `summarized_findings`

After `replay-evaluate`:

- inspect `status` first
- inspect `subject_type`
- inspect `mismatches_count`
- inspect `drift_reasons`
- read `explanation` after the structural mismatch fields

## Example Operator Flows

### Refresh, Checkpoint, And Health

```bash
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1 > /tmp/orchestrate-refresh.json
python -m json.tool /tmp/orchestrate-refresh.json
python -m json.tool state/runtime_orchestrator_checkpoint.json
```

Inspect in order:

1. `health.status`
2. `health.stale_reasons`
3. `checkpoint.last_error`
4. `checkpoint.last_websocket_event_at`
5. `checkpoint.subscribed_asset_ids`

### Paper Trade Then Freeze A Packet

```bash
python -m polymarket_arb.cli paper-trade --limit 5 > /tmp/paper-trade-rows.json
python -m json.tool /tmp/paper-trade-rows.json
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 5 > /tmp/paper-trade-packet.json
python -m json.tool /tmp/paper-trade-packet.json
```

Current behavior note:

- `paper-trade` and `review-packet --packet-type paper_trade` are two separate reads against the shipped paper-trade surface
- `review-packet` does not accept a prior `paper-trade` output file as input

### Baseline Vs Candidate Replay

```bash
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json > /tmp/review-baseline.json
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_candidate.json > /tmp/review-candidate.json
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/review-baseline.json --candidate-path /tmp/review-candidate.json > /tmp/replay-evaluation.json
python -m json.tool /tmp/replay-evaluation.json
```

## Checkpoint And Health

Checkpoint path:

- `state/runtime_orchestrator_checkpoint.json`

Current checkpoint fields to inspect first:

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

Current health states:

- `idle`
- `ok`
- `stale`

Current meanings:

- `idle`: both `last_scan_refresh_at` and `last_relationship_refresh_at` are still `null`
- `ok`: at least one refresh has run and there are no current stale reasons
- `stale`: at least one refresh has run and `stale_reasons` is non-empty

Important current behavior:

- `status` and `stale` are separate fields
- an untouched system can report `status = "idle"` and still return `stale = true` with never-refreshed reasons

Current stale reasons:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

## Failure-Mode Quick Reference

Triage order:

1. inspect `health.status`
2. inspect `health.stale_reasons`
3. inspect `checkpoint.last_error`
4. inspect refresh timestamps
5. inspect websocket timestamps and subscribed asset count only if subscriptions exist

`scan_never_refreshed`
: inspect whether `orchestrate-refresh` has been run at all, then inspect `checkpoint.last_scan_refresh_at` and `health.status`

`scan_refresh_overdue`
: inspect `checkpoint.last_scan_refresh_at`, the expected refresh cadence, and whether you are looking at the intended checkpoint file

`relationships_never_refreshed`
: inspect whether `orchestrate-refresh` has been run at all, then inspect `checkpoint.last_relationship_refresh_at`

`relationship_refresh_overdue`
: inspect `checkpoint.last_relationship_refresh_at`, the expected refresh cadence, and the checkpoint path

`websocket_never_received_event`
: inspect `checkpoint.subscribed_asset_ids`, `checkpoint.last_websocket_connect_at`, `checkpoint.last_error`, and the `--max-websocket-messages` value used

`websocket_event_overdue`
: inspect `checkpoint.last_websocket_event_at`, `checkpoint.subscribed_asset_ids`, `checkpoint.websocket_reconnect_count`, and `checkpoint.last_error`

`last_error_present`
: inspect `checkpoint.last_error` first, then inspect websocket disconnect and reconnect counters

`websocket_consumer_exited_without_messages`
: inspect `checkpoint.last_error`, `checkpoint.subscribed_asset_ids`, `checkpoint.last_websocket_connect_at`, `checkpoint.last_websocket_event_at`, and the `--max-websocket-messages` value used

Reporting note:

- `websocket_consumer_exited_without_messages` is stored in `checkpoint.last_error`
- health reports it through `last_error_present`, not as its own stale reason

## Review Discipline

- choose the packet subject type first, then generate baseline and candidate with that same subject type
- prefer fixture-backed packet generation when deterministic comparison matters
- inspect packet contents before running replay
- read `drift_reasons` before writing any summary of what changed
- do not describe replay output as strategy quality; it is a record-comparison tool

## Scope Boundary

This runbook documents the shipped baseline through Phase 10D freeze polish.

It does not introduce:

- Python behavior changes
- new routes
- new CLI commands
- policy changes
- live trading behavior
