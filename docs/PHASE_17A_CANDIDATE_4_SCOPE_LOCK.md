# Phase 17A — Candidate 4 Scope Lock

## 1) Current Repo Truth

- Current implementation branch: `phase-17a-candidate-4-scope-lock`
- Base branch: `phase-16a-candidate-3-scope-lock`
- Current base head: `66b9ce1`
- Candidate 3 is closed via `docs/PHASE_16F_CANDIDATE_3_CLOSEOUT.md`
- Candidate 3 delivered a bounded comparison artifact chain under
  `src/future_system/manual_gate/`:
  - comparison layer (`comparisons.py`)
  - comparison-report layer (`comparison_reports.py`)
  - comparison-bundle layer (`comparison_bundles.py`)
- Candidate 2 remains the upstream manual-gate artifact source surface
  (`ManualGateBundle` chain)
- `src/polymarket_arb/` remains frozen baseline and no-touch for this candidate

## 2) Candidate 4 Definition

Candidate 4 is a bounded, non-live, advisory **manual-gate comparison replay** foundation.

It defines deterministic replay scenarios over Candidate 2 / Candidate 3 artifact surfaces,
producing pure in-memory replay outputs for inspection only.

Candidate 4 must:

- accept typed scenario inputs grounded in existing Candidate 2 and Candidate 3 artifacts
- execute deterministic replay over comparison/report/bundle formatting flow
- expose explicit expected-vs-actual replay signals for bounded comparison dimensions
- remain strictly advisory (no decisions, no automation, no execution)

Candidate 4 is not a control plane and is not an execution path.

## 3) Why Candidate 4 Belongs After Candidate 3

Candidate 3 established deterministic comparison primitives and rendering surfaces:

1. `ManualGateComparison`
2. `ManualGateComparisonReport`
3. `ManualGateComparisonBundle`

A replay foundation belongs after Candidate 3 because scenario replay depends on stable,
already-defined comparison artifacts. Candidate 4 should orchestrate deterministic scenario
expression over these existing surfaces, not redefine comparison semantics.

## 4) Exact Allowed Scope

Candidate 4 scope is limited to deterministic, in-memory replay of bounded manual-gate
comparison scenarios over existing Candidate 2 / Candidate 3 outputs.

In-scope for Candidate 4:

- typed replay scenario model(s) that reference existing Candidate 2 bundle inputs and
  Candidate 3 bounded expectations
- one deterministic replay function that executes existing comparison/report/bundle chain
  for a scenario and returns a bounded replay artifact
- explicit replay output fields suitable for manual inspection of expected-vs-actual
  comparison behavior
- deterministic tests proving stable replay behavior and boundary compliance

Out-of-scope within Candidate 4:

- changing Candidate 2 packet/replay/report/bundle semantics
- changing Candidate 3 comparison/report/bundle semantics
- introducing runtime orchestration, persistence, external side effects, or live behavior

## 5) Explicit Non-Goals

Candidate 4 must not:

- modify any file under `src/polymarket_arb/`
- add routes, CLI commands, adapters, workflow engines, or runtime wiring
- add network calls, database writes, or filesystem writes in code
- add auth, credentials, keys, signing, order, submit, venue, or position semantics
- add approval automation, promotion automation, or control-plane behavior
- add scoring/ranking or policy enforcement behavior
- redesign Candidate 2/Candidate 3 artifacts instead of replaying them
- begin a further new candidate inside Candidate 4 implementation phases

## 6) Minimum Likely File Touch Set For 17B

Phase 17B should be the first code phase for Candidate 4.

Minimum likely file touch set:

```text
src/future_system/manual_gate/comparison_replay.py
src/future_system/manual_gate/__init__.py
tests/future_system/test_manual_gate_comparison_replay.py
docs/PHASE_17B_IMPLEMENTATION_LOG.md
```

Preferred responsibilities:

- `comparison_replay.py`
  - define bounded replay scenario/result model(s)
  - define one deterministic replay function over existing Candidate 2/Candidate 3 surfaces
- `test_manual_gate_comparison_replay.py`
  - prove deterministic replay outcomes for equal and differing bounded scenarios
  - prove pure in-memory boundary and forbidden-semantic guardrails
- `PHASE_17B_IMPLEMENTATION_LOG.md`
  - record touched files, exports, validation, and deferred items

## 7) Validation Expectations For 17B

Phase 17B must run and pass at minimum:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m pytest tests/future_system/test_manual_gate_comparison_replay.py -v
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

Candidate 4 must halt immediately if:

- any file under `src/polymarket_arb/` needs to change
- replay logic requires routes/CLI/adapters/runtime orchestration
- network/persistence/auth/signing/venue/order/position behavior becomes necessary
- Candidate 2 or Candidate 3 semantics must be rewritten instead of replayed
- implementation drifts into approval automation, policy enforcement expansion, or
  control-plane behavior
- file touches expand beyond bounded comparison replay foundation without explicit
  reapproval

A halt means: stop, do not commit, document the conflict, and request reauthorization.

## 9) Phase 17A Outcome

Phase 17A defines Candidate 4 only.

It does not begin implementation. It does not modify Candidate 2/Candidate 3 artifacts.
It does not widen baseline or runtime behavior.
