# Phase 16A — Candidate 3 Scope Lock

## 1) Current Repo Truth

- Current implementation branch: `phase-16a-candidate-3-scope-lock`
- Base branch: `phase-15a-manual-decision-gate-foundation`
- Current base head: `9f5c5d0`
- Candidate 2 is closed via `docs/PHASE_15H_CANDIDATE_2_CLOSEOUT.md`
- Candidate 2 delivered a bounded manual-gate artifact chain under
  `src/future_system/manual_gate/`:
  - packet layer
  - replay layer
  - report layer
  - bundle layer
  - replay-to-bundle helper
- `src/polymarket_arb/` remains the frozen baseline module tree for this track
  and remains no-touch

## 2) Candidate 3 Definition

Candidate 3 is a bounded, non-live, advisory **manual-gate comparison/diff** layer.

It compares two Candidate 2 manual-gate outputs deterministically and produces a
pure in-memory comparison artifact for inspection only.

Candidate 3 must:

- accept typed Candidate 2 outputs
- compute deterministic, reproducible differences
- preserve explicit reasons for matches/mismatches
- remain strictly advisory (no decisions, no automation, no execution)

Candidate 3 is not a control plane and is not an execution path.

## 3) Why Candidate 3 Belongs After Candidate 2

Candidate 2 established stable artifact surfaces for one manual-gate path:

1. `ManualGatePacket`
2. `ManualGateReplayResult`
3. `ManualGateReport`
4. `ManualGateBundle`
5. replay-to-bundle one-hop formatting

A comparison layer belongs after this because diffing is only meaningful once a
stable artifact chain exists. Candidate 3 should compare normalized Candidate 2
outputs, not rebuild upstream review or gate logic.

## 4) Exact Allowed Scope

Candidate 3 scope is limited to deterministic in-memory comparison of two Candidate 2
manual-gate outputs.

In-scope for Candidate 3:

- typed comparison input from Candidate 2 artifacts (primary surface should be
  `ManualGateBundle`)
- deterministic equality/difference evaluation over bounded fields
- explicit comparison output suitable for manual inspection
- deterministic tests proving stable behavior and boundary compliance

Out-of-scope within Candidate 3:

- changing Candidate 2 packet/replay/report/bundle semantics
- changing Candidate 1 review semantics
- introducing runtime orchestration, persistence, or external side effects

## 5) Explicit Non-Goals

Candidate 3 must not:

- modify any file under `src/polymarket_arb/`
- add routes, CLI commands, adapters, workflow engines, or runtime wiring
- add network calls, database writes, or filesystem writes in code
- add auth, credentials, keys, signing, order, submit, venue, or position semantics
- add approval automation, promotion automation, or control-plane behavior
- add scoring/ranking or policy enforcement beyond bounded artifact comparison
- begin a new candidate inside Candidate 3 implementation phases

## 6) Minimum Likely File Touch Set For 16B

Phase 16B should be the first code phase for Candidate 3.

Minimum likely file touch set:

```text
src/future_system/manual_gate/comparisons.py
src/future_system/manual_gate/__init__.py
tests/future_system/test_manual_gate_comparisons.py
docs/PHASE_16B_IMPLEMENTATION_LOG.md
```

Preferred responsibilities:

- `comparisons.py`
  - define a bounded comparison result model
  - define one deterministic compare function over two Candidate 2 outputs
- `test_manual_gate_comparisons.py`
  - prove deterministic comparison outcomes for equal and differing artifacts
  - prove pure in-memory boundary and forbidden-semantic guardrails
- `PHASE_16B_IMPLEMENTATION_LOG.md`
  - record files, exports, validation, and deferred items

## 7) Validation Expectations For 16B

Phase 16B must run and pass at minimum:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m pytest tests/future_system/test_manual_gate_comparisons.py -v
```

```bash
cd "/Users/muhammadaatif/polymarket-arb"
git diff --name-only HEAD | grep "src/polymarket_arb" && echo "VIOLATION: baseline touched" || echo "OK: baseline clean"
```

```bash
cd "/Users/muhammadaatif/polymarket-arb"
grep -r "from polymarket_arb\|import polymarket_arb" src/future_system/ && echo "VIOLATION: cross-import" || echo "OK: no cross-imports"
```

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
make validate
```

And inspect final touched-file set:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
git status -sb
git diff --name-only HEAD
```

## 8) Halt Conditions

Candidate 3 must halt immediately if:

- any file under `src/polymarket_arb/` needs to change
- comparison logic requires routes/CLI/adapters/runtime orchestration
- network/persistence/auth/signing/venue/order/position behavior becomes necessary
- Candidate 2 semantics must be rewritten instead of compared
- implementation drifts into approval automation or control-plane behavior
- file touches expand beyond the bounded comparison layer without explicit reapproval

A halt means: stop, do not commit, document the conflict, and request reauthorization.

## 9) Phase 16A Outcome

Phase 16A defines Candidate 3 only.

It does not begin implementation. It does not modify Candidate 2 artifacts. It does
not widen baseline or runtime behavior.
