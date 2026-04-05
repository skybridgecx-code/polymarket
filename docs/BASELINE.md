# Baseline

## Current Shipped System

This document is the official frozen baseline for the shipped read-only system.

The system currently does:

- discover active Polymarket events and markets from public APIs
- fetch order books and fee rates from the public CLOB
- build fee-aware opportunity candidates with explanations and rejection reasons
- discover wallet seeds from leaderboard and holder data
- ingest normalized wallet activity
- score explainable leader/follower relationships from normalized activity
- generate paper-trade execution plans and simulated fill outcomes
- apply a deterministic policy decision layer to final paper-trade results
- build deterministic review packets and replay evaluations
- expose the results through CLI commands and a thin FastAPI API
- run bounded refresh cycles with checkpoint-safe websocket consumption

Operator entrypoint and read order:

1. [README.md](/Users/muhammadaatif/polymarket-arb/README.md)
2. [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)
3. [docs/BASELINE.md](/Users/muhammadaatif/polymarket-arb/docs/BASELINE.md)
4. [ARCHITECTURE.md](/Users/muhammadaatif/polymarket-arb/ARCHITECTURE.md)
5. [CODEX_HANDOFF.md](/Users/muhammadaatif/polymarket-arb/CODEX_HANDOFF.md)

The system explicitly does not do:

- place orders
- sign transactions
- submit live orders
- ingest private data
- authenticate users
- run a UI
- run an always-on worker system
- maintain a broad database or analytical warehouse

In scope:

- read-only ingestion
- deterministic analytics and simulation outputs
- thin operator CLI and API surfaces
- bounded checkpoint-safe refresh orchestration
- operator documentation and review discipline

Not in scope:

- live trading
- auth
- private keys
- real order submission
- UI
- background workers
- broad persistence expansion

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
- `policy_decision`

`policy_decision` is applied after simulation, not before planning or simulation. It records one of:

- `allow`: upstream paper-trade result was accepted and passed policy
- `hold`: policy-only block such as active circuit breaker or slippage above configured cap
- `deny`: upstream paper-trade result was already rejected

The policy decision also records:

- manual override fields for audit purposes only
- circuit-breaker state fields

Manual override fields are recorded only and are not operationalized. Circuit-breaker state can force `hold`.

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

Current health states derived from the checkpoint are:

- `idle`
- `ok`
- `stale`

Current health meanings:

- `idle`: both `last_scan_refresh_at` and `last_relationship_refresh_at` are `null`
- `ok`: refresh data exists and no stale reasons are active
- `stale`: refresh data exists and stale reasons are active

Current stale reasons:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

Current code behavior note:

- `status` and `stale` are separate fields
- a never-run system can still report `status = "idle"` while carrying never-refreshed stale reasons

## Operator Runbook

The canonical operator guide for runtime expectations, command selection, checkpoint inspection, health interpretation, checklists, examples, and failure-mode triage is:

- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

## Repo Operating Rules

- keep the system read-only
- keep logic deterministic where possible
- keep raw payload handling separate from scoring
- keep ingestion separate from relationship scoring
- keep route layer thin over services
- preserve weak or rejected outputs unless a future contract explicitly changes visibility
- do not make fake precision claims in outputs or docs
- do not describe policy as changing planner or simulator formulas when it only evaluates final paper-trade results

## Recommended Next Step

After this frozen baseline, the strongest next move is bounded operator validation discipline:

- bounded operator smoke-test workflow
- fixture-backed runbook verification
- validation discipline around checkpoint and replay review
- no new scoring or live behavior

Do not move into trading or new scoring before that operator layer is easier to inspect and validate.
