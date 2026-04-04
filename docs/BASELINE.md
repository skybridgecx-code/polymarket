# Baseline

## Frozen Baseline Summary

This document freezes the current shipped system as the official read-only baseline.

The system currently does:

- discover active Polymarket events and markets from public APIs
- fetch order books and fee rates from the public CLOB
- build fee-aware opportunity candidates with explanations and rejection reasons
- discover wallet seeds from leaderboard and holder data
- ingest normalized wallet activity
- score explainable leader/follower relationships from normalized activity
- generate paper-trade execution plans and simulated fill outcomes
- build deterministic review packets and replay evaluations
- expose the results through CLI commands and a thin FastAPI API
- run bounded refresh cycles with checkpoint-safe websocket consumption

The system explicitly does not do:

- place orders
- sign transactions
- submit live orders
- ingest private data
- authenticate users
- run a UI
- run an always-on worker system
- maintain a broad database or analytical warehouse

## Official Commands

Setup and validation:

```bash
make setup
source .venv/bin/activate
make validate
```

CLI:

```bash
python -m polymarket_arb.cli scan --limit 5
python -m polymarket_arb.cli wallet-backfill --limit 10
python -m polymarket_arb.cli detect-copiers --limit 10
python -m polymarket_arb.cli paper-trade --limit 5
python -m polymarket_arb.cli review-packet --packet-type opportunities --limit 5
python -m polymarket_arb.cli replay-evaluate --baseline-path /tmp/baseline.json --candidate-path /tmp/candidate.json
python -m polymarket_arb.cli orchestrate-refresh --scan-limit 5 --relationship-limit 10 --max-websocket-messages 1
```

API:

```bash
python -m uvicorn polymarket_arb.api.main:app --reload
```

## Official Routes

- `GET /health`
- `GET /opportunities`
- `GET /wallets/backfill`
- `GET /relationships/copiers`

## Output Contracts

### Opportunities

Each candidate includes:

- `event_slug`
- `opportunity_type`
- `legs`
- `gross_edge_cents`
- `estimated_fee_cents`
- `net_edge_cents`
- `capacity_shares_or_notional`
- `status`
- `rejection_reason`
- `explanation`

### Wallet Backfill

Wallet backfill includes:

- `selected_wallets`
- `wallet_seeds`
- `wallet_activities`

Seed and activity records preserve normalized wallet identifiers, timestamps, and source references.

### Relationships

Each relationship includes:

- `leader_wallet`
- `follower_wallet`
- `relationship_type`
- `matched_events_count`
- `matched_legs_count`
- `lag_summary_seconds`
- `confidence_score`
- `status`
- `rejection_reason`
- `explanation`
- `evidence`

### Paper Trade

Each paper-trade result includes:

- `plan_id`
- `source_opportunity_reference`
- `opportunity_type`
- `proposed_legs`
- `proposed_size`
- `estimated_entry_cost`
- `estimated_fees`
- `slippage_assumption`
- `status`
- `rejection_reason`
- `explanation`
- `risk_flags`
- `simulated_result`

### Review Packets

Each review packet includes:

- `packet_id`
- `packet_type`
- `created_at`
- `source_references`
- `summarized_findings`
- `raw_result_references`
- `embedded_records`
- `status`
- `notes`

### Replay Evaluation

Each replay evaluation includes:

- `evaluation_id`
- `subject_type`
- `compared_records_count`
- `matches_count`
- `mismatches_count`
- `drift_reasons`
- `status`
- `explanation`

## Orchestration Baseline

`RefreshOrchestratorService` is bounded by input limits and websocket message count. It is not an always-on scheduler.

Checkpoint behavior:

- writes JSON only
- resumes from known subscribed asset ids if needed
- marks stale states explicitly
- exposes reconnect, disconnect, and last-error state through `/health`

Default checkpoint file:

- `state/runtime_orchestrator_checkpoint.json`

## Repo Operating Rules

- keep the system read-only
- keep logic deterministic where possible
- keep raw payload handling separate from scoring
- keep ingestion separate from relationship scoring
- keep route layer thin over services
- preserve weak or rejected outputs unless a future contract explicitly changes visibility
- do not make fake precision claims in outputs or docs

## Recommended Next Phase

After this paper-trade layer, the strongest next move is Phase 7C operator hardening:

- deployment and runtime docs
- packaging and release hygiene
- observability and operational guidance

Do not move into trading or new scoring before that operator layer is cleaner and easier to run.
