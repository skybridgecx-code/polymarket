# Operator Validation

## Purpose

This document defines the bounded validation layer for the shipped operator surface.

It is verification-only. It does not add:

- new routes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior

## Validation Order

Run validation in this order:

1. core repo validation
2. bounded refresh and checkpoint inspection
3. `/health` inspection
4. paper-trade inspection
5. review-packet inspection
6. replay-evaluate inspection

## Core Repo Validation

Command:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
make validate
```

Sanity check:

- command exits successfully
- `ruff`, `mypy`, and `pytest` all pass

## Bounded Refresh Validation

Command:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1 > /tmp/operator_refresh.json
python -m json.tool /tmp/operator_refresh.json
python -m json.tool state/runtime_orchestrator_checkpoint.json
```

Sanity checks in `/tmp/operator_refresh.json`:

- top-level keys include `scan_limit`, `relationship_limit`, `max_websocket_messages`, `checkpoint`, `health`, `opportunities_count`, and `relationships_count`
- `scan_limit` equals `5`
- `relationship_limit` equals `10`
- `max_websocket_messages` equals `1`
- `checkpoint` is a JSON object
- `health` is a JSON object

Sanity checks in `state/runtime_orchestrator_checkpoint.json`:

- `checkpoint_written_at` is present
- `last_scan_refresh_at` is present
- `last_relationship_refresh_at` is present
- `last_refresh_limit` equals `5`
- `last_relationship_limit` equals `10`
- `stale_reasons` is present as a list

## `/health` Validation

Commands:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m uvicorn polymarket_arb.api.main:app --reload
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

Sanity checks:

- response includes `status`
- response includes `stale`
- response includes `stale_reasons`
- response includes `checkpoint_path`
- response includes `last_error`
- response includes `websocket_reconnect_count`
- response includes `websocket_disconnect_count`
- response includes `subscribed_asset_ids_count`

Current valid `status` values:

- `idle`
- `ok`
- `stale`

Current valid stale-reason values:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

## Paper-Trade Validation

Command:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m polymarket_arb.cli paper-trade --limit 5 --fixture-path tests/fixtures/scenarios/phase7b_paper_trade.json > /tmp/operator_paper_trade.json
python -m json.tool /tmp/operator_paper_trade.json
```

Sanity checks on each row:

- `status` is present
- `rejection_reason` is present, including `null` when not rejected
- `explanation` is present
- `risk_flags` is present
- `simulated_result` is present
- `policy_decision` is present

Sanity checks on `policy_decision`:

- decision record is present on every final row
- decision value is one of `allow`, `hold`, or `deny`

## Review-Packet Validation

Command:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json > /tmp/operator_review_packet.json
python -m json.tool /tmp/operator_review_packet.json
```

Sanity checks:

- `packet_id` is present
- `packet_type` equals `paper_trade`
- `created_at` is present
- `source_references` is present
- `summarized_findings` is present
- `status` is present
- `notes` is present

## Replay-Evaluate Validation

Commands:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_baseline.json > /tmp/operator_replay_baseline.json
python -m polymarket_arb.cli review-packet --packet-type paper_trade --limit 10 --fixture-path tests/fixtures/scenarios/phase8_review_records_candidate.json > /tmp/operator_replay_candidate.json
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/operator_replay_baseline.json --candidate-path /tmp/operator_replay_candidate.json > /tmp/operator_replay_eval.json
python -m json.tool /tmp/operator_replay_eval.json
```

Sanity checks:

- `evaluation_id` is present
- `subject_type` equals `paper_trade`
- `compared_records_count` is present
- `matches_count` is present
- `mismatches_count` is present
- `drift_reasons` is present
- `status` is present
- `explanation` is present

## Failure-Oriented Checks

If `health.stale_reasons` is non-empty:

- inspect `checkpoint.last_error` first
- inspect `checkpoint.last_scan_refresh_at`
- inspect `checkpoint.last_relationship_refresh_at`
- inspect `checkpoint.last_websocket_event_at` only when subscriptions exist

If `last_error` equals `websocket_consumer_exited_without_messages`:

- confirm the run used `--max-websocket-messages 1`
- inspect `checkpoint.subscribed_asset_ids`
- inspect `checkpoint.last_websocket_connect_at`
- inspect `checkpoint.last_websocket_event_at`

## Scope Boundary

This validation layer verifies the shipped operator surface only.

It does not authorize:

- new routes
- new CLI commands
- policy changes
- scoring changes
- live execution behavior
