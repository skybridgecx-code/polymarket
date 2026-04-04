# Codex Handoff

## Current Status

Phase 1 is implemented and bounded to read-only scanner infrastructure.

Implemented:

- project scaffolding
- typed settings
- Gamma events read client
- CLOB orderbook read client
- raw payload wrappers
- normalized event, market, and book models
- deterministic `scan` CLI output
- fixture-backed unit tests

Not implemented yet:

- wallet analytics
- API server
- WebSocket ingestion
- ranking engine
- execution or trading

## Read First

- `ARCHITECTURE.md`
- `ROADMAP.md`
- `CODEX_HANDOFF.md`
- `README.md`

## Guardrails

- stay within one phase at a time
- keep the system read-only
- keep raw payload evidence separable from normalized models
- do not introduce trading, auth, or UI work early
- do not blur Phase 2 opportunity scoring into the client layer

## Validation Contract

```bash
make validate
python -m polymarket_arb.cli scan --limit 5
```

## Next Bounded Prompt

Phase 2 only:

- add neg-risk and complement analyzers
- add fee-aware edge math
- add liquidity screening
- add rejection reasons and explanation fields
- add deterministic scenario tests

Do not add wallets, API, WebSocket, or execution code in that phase.

