# Phase 18A — Candidate 5 Scope Lock

## 1) Current Repo Truth

- Current implementation branch: `phase-18a-candidate-5-scope-lock`
- Base branch: `phase-17a-candidate-4-scope-lock`
- Current base head: `a94c087`
- Candidate 4 is closed via `docs/PHASE_17D_CANDIDATE_4_CLOSEOUT.md`
- Candidate 4 delivered a bounded manual-gate comparison replay foundation under
  `src/future_system/manual_gate/`:
  - replay scenario model (`ManualGateComparisonReplayScenario`)
  - replay result model (`ManualGateComparisonReplayResult`)
  - single replay function (`run_manual_gate_comparison_replay(...)`)
- Candidate 3 remains the upstream comparison artifact chain
  (`ManualGateComparison`, `ManualGateComparisonReport`, `ManualGateComparisonBundle`)
- `src/polymarket_arb/` remains the frozen baseline module tree and remains no-touch

## 2) Candidate 5 Definition

Candidate 5 is a bounded, non-live, advisory **manual-gate comparison replay report** layer.

It renders deterministic replay outputs from Candidate 4 into pure in-memory,
inspection-only report artifacts.

Candidate 5 must:

- accept typed Candidate 4 replay outputs as the primary input surface
- render deterministic replay-report fields for manual inspection
- preserve explicit bounded replay details (scenario identity and replay outcome summary)
- remain strictly advisory (no decisions, no automation, no execution)

Candidate 5 is not a control plane and is not an execution path.

## 3) Why Candidate 5 Belongs After Candidate 4

Candidate 4 established a stable replay output surface:

1. `ManualGateComparisonReplayScenario`
2. `ManualGateComparisonReplayResult`
3. `run_manual_gate_comparison_replay(...)`

A replay report layer belongs after Candidate 4 because rendering is only meaningful once
replay outputs are stable and deterministic. Candidate 5 should render existing replay
outputs, not redefine replay/comparison semantics.

## 4) Exact Allowed Scope

Candidate 5 scope is limited to deterministic in-memory rendering of one Candidate 4 replay
result into a bounded report artifact.

In-scope for Candidate 5:

- typed replay-report output model(s) derived from Candidate 4 replay result fields
- one deterministic replay-report render function over a single replay result
- explicit replay-report output suitable for manual inspection
- deterministic tests proving stable behavior and boundary compliance

Out-of-scope within Candidate 5:

- changing Candidate 4 replay semantics or model behavior
- changing Candidate 3 comparison/report/bundle semantics
- introducing runtime orchestration, persistence, or external side effects

## 5) Explicit Non-Goals

Candidate 5 must not:

- modify any file under `src/polymarket_arb/`
- add routes, CLI commands, adapters, workflow engines, or runtime wiring
- add network calls, database writes, or filesystem writes in code
- add auth, credentials, keys, signing, order, submit, venue, or position semantics
- add approval automation, promotion automation, policy behavior, or control-plane behavior
- add replay pack runners or multi-scenario orchestration
- begin a new candidate inside Candidate 5 implementation phases

## 6) Minimum Likely File Touch Set For 18B

Phase 18B should be the first code phase for Candidate 5.

Minimum likely file touch set:

```text
src/future_system/manual_gate/comparison_replay_reports.py
src/future_system/manual_gate/__init__.py
tests/future_system/test_manual_gate_comparison_replay_reports.py
docs/PHASE_18B_IMPLEMENTATION_LOG.md
```

Preferred responsibilities:

- `comparison_replay_reports.py`
  - define a bounded replay-report model
  - define one deterministic render function over `ManualGateComparisonReplayResult`
- `test_manual_gate_comparison_replay_reports.py`
  - prove deterministic render behavior for equal and differing replay outcomes
  - prove pure in-memory boundary and forbidden-semantic guardrails
- `PHASE_18B_IMPLEMENTATION_LOG.md`
  - record files, exports, validation, and deferred items

## 7) Validation Expectations For 18B

Phase 18B must run and pass at minimum:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m pytest tests/future_system/test_manual_gate_comparison_replay_reports.py -v
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

Candidate 5 must halt immediately if:

- any file under `src/polymarket_arb/` needs to change
- replay-report rendering requires routes/CLI/adapters/runtime orchestration
- network/persistence/auth/signing/venue/order/position behavior becomes necessary
- Candidate 4 replay semantics must be rewritten instead of rendered
- implementation drifts into approval automation, policy enforcement, or control-plane behavior
- file touches expand beyond bounded replay-report rendering without explicit reapproval

A halt means: stop, do not commit, document the conflict, and request reauthorization.

## 9) Phase 18A Outcome

Phase 18A defines Candidate 5 only.

It does not begin implementation. It does not modify Candidate 3/Candidate 4 artifacts.
It does not widen baseline or runtime behavior.
