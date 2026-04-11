# Phase 18F — Theme-Linked Crypto Evidence Assembly

## Role
You are the implementation engine, not the architect.

Do not redesign the system.
Do not widen scope.
Do not touch unrelated modules.
Preserve current boundaries.

## Architectural truth
- `src/polymarket_arb/*` remains the bounded Polymarket intelligence/opportunity module.
- `src/future_system/theme_graph/*` is the canonical theme-linking layer.
- `src/future_system/evidence/*` is the canonical Polymarket evidence contract + assembly layer.
- `src/future_system/divergence/*` is the deterministic disagreement layer for theme evidence packets.
- `src/future_system/crypto_adapter/*` is the normalized crypto source boundary.
- This phase adds the missing bridge from theme-linked asset definitions + normalized crypto states into a canonical theme-scoped crypto evidence packet.
- This phase is deterministic assembly only.
- Do not add cross-market comparison, live fetches, websocket logic, reasoning, policy, execution, UI, storage, or network clients.

## Why this phase exists
The system now knows:
- what themes are
- what linked crypto assets are
- how to parse normalized crypto market states

But it still cannot answer:
- what is the current crypto evidence for this theme
- which linked crypto symbols matched
- how fresh/liquid those linked proxies are
- what aggregate crypto proxy state should be compared later against Polymarket

This phase creates that canonical crypto evidence layer.

## Phase objective
Build `src/future_system/crypto_evidence/` so the system can:

1. accept a `ThemeLinkPacket`
2. accept one or more `NormalizedCryptoMarketState` inputs
3. select only the crypto states relevant to the linked theme assets
4. compute deterministic freshness/liquidity summaries for matched crypto proxies
5. emit a canonical `ThemeCryptoEvidencePacket`

This phase does not compare crypto to Polymarket.
This phase does not merge source families.
This phase does not do reasoning or policy.

## In scope

Create these files if they do not already exist:

- `src/future_system/crypto_evidence/__init__.py`
- `src/future_system/crypto_evidence/models.py`
- `src/future_system/crypto_evidence/assembler.py`
- `src/future_system/crypto_evidence/scoring.py`

Create tests:

- `tests/future_system/test_crypto_evidence_models.py`
- `tests/future_system/test_crypto_evidence_assembler.py`
- `tests/future_system/test_crypto_evidence_scoring.py`

Create fixtures:

- `tests/fixtures/future_system/crypto/theme_crypto_states.json`

Follow existing repo style and fixture conventions if they already exist.

## Out of scope
Do not build or touch:

- live HTTP clients
- websocket clients
- scheduler / polling jobs
- mixed-source evidence merger
- Polymarket-vs-crypto comparison
- news adapters
- reasoning / prompts / LLM logic
- policy engine
- execution logic
- CLI/API surfaces
- dashboard/UI
- persistence/database
- repo-wide refactors

## Do not touch
- `src/polymarket_arb/*`
- trade service / live order code
- existing CLI behavior
- unrelated phase docs

If imports require tiny changes elsewhere, keep them minimal and explain them.

## Required models

Implement strongly typed models using existing repo conventions.

### 1. `CryptoProxyEvidence`
Represents one linked crypto proxy’s theme-scoped evidence.

Suggested fields:
- `symbol: str`
- `market_type: Literal["spot", "perp"]`
- `exchange: str`
- `role: Literal["primary_proxy", "confirmation_proxy", "hedge_proxy", "context_only"]`
- `direction_if_theme_up: Literal["up", "down", "mixed", "unknown"]`
- `last_price: float | None`
- `mid_price: float | None`
- `funding_rate: float | None`
- `open_interest: float | None`
- `liquidity_score: float`
- `freshness_score: float`
- `flags: list[str]`
- `is_primary: bool = False`

### 2. `ThemeCryptoEvidencePacket`
Canonical crypto evidence output for one theme.

Suggested fields:
- `theme_id: str`
- `primary_symbol: str | None`
- `proxy_evidence: list[CryptoProxyEvidence]`
- `matched_symbols: list[str]`
- `liquidity_score: float`
- `freshness_score: float`
- `coverage_score: float`
- `flags: list[str]`
- `explanation: str`

### 3. `CryptoEvidenceAssemblyError`
Raised when assembly cannot build a valid packet from the provided theme links and normalized crypto states.

## Assembly behavior

Implement deterministic assembly from:
- `ThemeLinkPacket`
- sequence of `NormalizedCryptoMarketState` or plain mappings that validate into that model

Rules:

1. Only include crypto states whose symbols match linked theme asset symbols where:
   - asset type is relevant to crypto proxies (`spot` or `perp`)
   - symbol matches exactly after deterministic normalization

2. If no linked crypto states match:
   - raise `CryptoEvidenceAssemblyError`
   - do not invent a packet

3. Only use theme asset links that are crypto-relevant.
Ignore non-crypto asset links like equities, yields, FX, etc.

4. Select primary proxy deterministically:
   - `primary_proxy` role wins over others
   - among same role, highest liquidity score wins
   - ties break by symbol ascending

5. Compute freshness score deterministically from `snapshot_at` age relative to an explicit `reference_time` input.
   - no hidden use of current system time in core logic
   - keep scoring simple and explicit

Suggested buckets:
- <= 5 minutes: 1.00
- <= 30 minutes: 0.80
- <= 2 hours: 0.50
- > 2 hours: 0.20 and add stale flag

6. Compute liquidity score deterministically and simply.
Use available crypto inputs like:
- bid/ask spread if bid and ask exist
- volume_24h
- open_interest for perps when present

Keep this explicit and bounded.
Do not over-engineer a fake quant model.

7. Coverage score:
   - deterministic bounded score in `[0.0, 1.0]`
   - based on proportion of linked crypto symbols actually matched
   - for example: matched / linked-crypto-assets
   - if there are no crypto-linked assets in the theme packet, raise `CryptoEvidenceAssemblyError`

8. Packet-level scores:
   - liquidity score = mean of proxy liquidity scores
   - freshness score = mean of proxy freshness scores
   - all bounded in `[0.0, 1.0]`

9. Surface explicit flags for:
   - stale snapshot
   - missing mid/last price
   - low liquidity
   - no crypto-linked assets
   - incomplete linked symbol coverage

10. Explanation:
   Produce a short deterministic explanation string summarizing:
   - matched symbol count
   - primary proxy
   - packet scores
   - key flags

## Scoring requirements
Create small pure functions in `scoring.py`.

Suggested functions:
- `compute_crypto_freshness_score(...)`
- `compute_crypto_liquidity_score(...)`
- `compute_crypto_coverage_score(...)`

Keep them:
- deterministic
- bounded
- easy to inspect
- free of side effects

No randomization.
No hidden global time.
No network assumptions.

## Symbol matching and normalization
Keep normalization simple and deterministic.

Examples:
- `BTC` theme asset should match `BTC-USD` spot and `BTC-PERP` perp only if your matching rule explicitly supports base-asset matching
- or require exact symbol equality if you choose a stricter rule

Pick one clear rule and apply it consistently in code and tests.
Do not use fuzzy matching.

Preferred approach:
- allow a linked asset symbol like `BTC` to match normalized crypto states whose `base_asset == BTC`
- retain exact symbol matching when the linked symbol itself is already a full market symbol like `BTC-PERP`

Keep this logic small and explicit.

## Test requirements

### `test_crypto_evidence_models.py`
Cover:
- valid packet models
- invalid bounded scores rejected
- required fields enforced

### `test_crypto_evidence_assembler.py`
Cover:
- linked crypto states selected correctly
- non-crypto theme assets ignored
- no matches raises `CryptoEvidenceAssemblyError`
- no crypto-linked assets raises `CryptoEvidenceAssemblyError`
- primary proxy selection deterministic
- coverage score deterministic
- stale and incomplete-coverage flags surface correctly
- explanation string deterministic

### `test_crypto_evidence_scoring.py`
Cover:
- freshness score buckets
- liquidity score bounded in `[0,1]`
- coverage score bounded in `[0,1]`
- deterministic outputs for known inputs

## Fixtures
Create a small deterministic fixture set with at least:
- one BTC spot state
- one BTC perp state
- one ETH spot state
- one unrelated crypto state
- timestamps that allow at least one stale case in tests

## Constraints
- keep code small
- prefer pure functions
- do not add new dependencies unless absolutely necessary
- do not fetch live data
- do not touch `src/polymarket_arb/*`
- do not implement mixed-source comparison in this phase

## Acceptance criteria
This phase is complete only if all are true:

1. `src/future_system/crypto_evidence/*` exists with the files listed above
2. typed models validate correctly
3. assembler consumes `ThemeLinkPacket` + normalized crypto states
4. only linked crypto-relevant assets are included
5. deterministic primary proxy selection works
6. freshness/liquidity/coverage scores are deterministic and bounded
7. explicit flags surface correctly
8. tests pass
9. no unrelated modules were modified
10. `src/polymarket_arb/*` remains untouched

## Validation
Before finishing:
- inspect repo commands and run the narrowest relevant checks
- run targeted tests first
- run narrow ruff check for touched files
- run narrow mypy check for the new crypto evidence module if mypy is already in use

At minimum, run:
- targeted pytest for the new crypto evidence tests
- narrow ruff check for touched files
- narrow mypy check for the new crypto evidence module

## Final output format
Return only:
1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. any deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched

Do not widen the phase.
Do not start Polymarket-vs-crypto comparison.
Do not start reasoning or policy.
Complete only this bounded phase.
