# Architecture

## What Matters

The system is a Python-first, read-only analytics stack. It exists to turn public Polymarket market and wallet data into deterministic operator outputs with explicit evidence, explanations, and rejection reasons.

This repo is not an execution system.

## Current Shipped System

The frozen baseline contains eight bounded layers:

1. Public ingestion clients
2. Normalization
3. Opportunity scoring
4. Paper-trade execution research
5. Wallet relationship scoring
6. Review and replay evaluation
7. Thin operator surfaces
8. Bounded refresh orchestration

## Module Boundaries

### `src/polymarket_arb/clients/`

External read-only adapters:

- `gamma.py`: active event and market discovery
- `clob.py`: order books and fee rates
- `data_api.py`: leaderboard, holders, and wallet activity
- `ws_market.py`: bounded market websocket consumption

Rules:

- no scoring logic
- no normalization logic beyond trivial transport handling
- no business decisions about acceptance or rejection

### `src/polymarket_arb/ingest/`

Normalization boundary:

- converts raw external payloads into internal normalized models
- preserves source identifiers and timestamps
- handles sparse or inconsistent public payloads explicitly

Rules:

- no scoring
- no route logic
- no orchestration logic

### `src/polymarket_arb/opportunities/`

Opportunity engine boundary:

- binary complement analysis
- neg-risk basket analysis
- fee calculation
- liquidity and slippage screening
- ranked output with explanation and rejection metadata

Rules:

- consumes normalized market data only
- no client calls
- no route logic

### `src/polymarket_arb/execution/`

Paper-trade research boundary:

- execution plan generation from originating opportunities
- explicit slippage assumptions
- simulated fills
- existing planner and simulator rejection behavior
- post-simulation policy evaluation and decision records

Rules:

- paper trading only
- no auth
- no private keys
- no order placement
- keep plan generation separate from simulation
- keep policy evaluation separate from planner and simulator formulas
- manual override fields are recorded only and not operationalized

### `src/polymarket_arb/review/`

Review and replay boundary:

- packet building for opportunities, relationships, and paper-trade results
- deterministic embedded export records
- replay comparison with explicit drift reasons

Rules:

- keep review packet building separate from replay comparison
- preserve source references and evidence fields
- no new scoring logic

### `src/polymarket_arb/relationships/`

Relationship engine boundary:

- same-leg same-side matching
- bounded lag-window matching
- repeated-event relationship scoring
- explicit false-positive guards
- evidence-backed accepted or rejected reports

Rules:

- consumes normalized wallet activity only
- no ingestion logic
- no API logic

### `src/polymarket_arb/services/`

Composition layer:

- `scan_service.py`: clients + normalization + opportunity engine
- `wallet_backfill_service.py`: wallet seed discovery + activity collection
- `copier_detection_service.py`: wallet backfill + relationship engine
- `orchestration_service.py`: bounded refresh cycle + checkpoint/state handling

Rules:

- service layer composes existing modules
- service layer should not redefine scoring formulas already owned by engines
- route and CLI layers should call services rather than duplicate logic

### `src/polymarket_arb/api/`

Thin FastAPI operator surface:

- `GET /health`
- `GET /opportunities`
- `GET /wallets/backfill`
- `GET /relationships/copiers`

Rules:

- no new scoring
- no heavy orchestration logic
- preserve explanation, rejection, and evidence fields

### `src/polymarket_arb/models/`

Type boundary:

- `raw.py`: external payload wrappers
- `normalized.py`: normalized market and wallet records
- `opportunity.py`: opportunity output models
- `relationship.py`: relationship output models
- `orchestration.py`: websocket event, checkpoint, and health models

## Data Flow

### Opportunity Path

`GammaClient` + `ClobClient` -> raw models -> normalization -> `OpportunityEngine` -> `ScanService` -> CLI/API

### Wallet Path

`DataApiClient` + `GammaClient` -> raw models -> normalization -> `WalletBackfillService` -> CLI/API

### Relationship Path

`WalletBackfillService` -> normalized wallet activity -> `RelationshipEngine` -> `CopierDetectionService` -> CLI/API

### Paper-Trade Path

`ScanService` or fixture input -> `ExecutionPlanBuilder` -> `PaperTradeSimulator` -> `PolicyGuardrailService` -> `PaperTradeService` -> CLI

The execution layer still preserves existing planner and simulator outcomes. `ExecutionPlanBuilder` can reject plans, and `PaperTradeSimulator` can still reject simulated results based on the existing formulas. `PolicyGuardrailService` is an added step after simulation; it does not replace or bypass planner/simulator rejection logic.

Policy intent on final paper-trade rows:

- `allow`: accepted simulated result that passes policy
- `hold`: policy-only block such as active circuit breaker or slippage above configured cap
- `deny`: upstream rejected simulated result

Circuit-breaker state is recorded in the decision record and can force `hold`. Manual override fields are also recorded in the decision record but are not operationalized.

### Review Path

existing result outputs or fixtures -> `ReviewPacketService` -> packet JSON

### Replay Path

baseline packet JSON + candidate packet JSON -> `ReplayEvaluationService` -> evaluation JSON

### Orchestration Path

`RefreshOrchestratorService` -> `ScanService` + `CopierDetectionService` -> derived websocket asset ids -> `MarketWebSocketClient` -> checkpoint file -> `/health`

## Checkpoint And Staleness Model

Checkpointing is intentionally small. The repo stores only what is required to resume bounded refresh safely:

- refresh timestamps
- websocket connect and event timestamps
- reconnect and disconnect counters
- subscribed asset ids
- last limits used
- last error
- stale reasons

Default location:

- `state/runtime_orchestrator_checkpoint.json`

Health states are deterministic from checkpoint content and current time:

- `idle`
- `ok`
- `stale`

Health interpretation is current-code specific:

- `idle`: both `last_scan_refresh_at` and `last_relationship_refresh_at` are still missing
- `ok`: at least one refresh exists and `_stale_reasons()` is empty
- `stale`: at least one refresh exists and `_stale_reasons()` is non-empty

Current stale reasons come directly from `RefreshOrchestratorService._stale_reasons()`:

- `scan_never_refreshed`
- `scan_refresh_overdue`
- `relationships_never_refreshed`
- `relationship_refresh_overdue`
- `websocket_never_received_event`
- `websocket_event_overdue`
- `last_error_present`

Operator note:

- `status` is not the same field as `stale`
- a clean never-run checkpoint can still report `status = "idle"` with never-refreshed stale reasons present

Operator workflow details live in:

- [docs/OPERATOR_RUNBOOK.md](/Users/muhammadaatif/polymarket-arb/docs/OPERATOR_RUNBOOK.md)

That runbook is intentionally documentation-only. It adds command-selection guidance and bounded example workflows on top of the existing operator surface; it does not alter orchestration, scoring, review, or policy behavior.

Phase 10C extends that same docs-only layer with pre-run and post-run checklists plus failure-mode triage guidance grounded in the current checkpoint and `last_error` fields.

## Explicit Non-Goals

- trading
- live execution
- auth
- UI
- broad persistence
- background job platform
- strategy execution
- hidden filtering of weak or rejected outputs

## Validation Boundary

Baseline validation is:

- `make validate`
- CLI smoke runs
- local API smoke runs

Future phases should preserve this separation. If a new feature needs changes across clients, normalization, engines, services, and routes all at once, that is a design smell and should be challenged first.
