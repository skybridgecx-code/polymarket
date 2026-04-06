# Phase 15A — Candidate 2 Bootstrap And Scope Lock

## Current Repo Truth

- the frozen baseline branch remains trusted and separate
- `src/polymarket_arb/` remains no-touch for this implementation track
- Candidate 1 is complete and closed as a bounded non-live review/replay foundation
- Candidate 1 added a future-system-only review stack under `src/future_system/`
- Candidate 1 did not add live-capable behavior, venue-facing actions, auth,
  signing, order submission, routes, CLI commands, persistence, or runtime automation
- Candidate 2 must be defined as a separate bounded candidate before any code starts

## Candidate 2 Definition

Candidate 2 is a non-live manual decision-gate foundation.

It consumes Candidate 1 review outputs and produces bounded manual gate packets for
inspection. It is advisory only. It does not approve, promote, execute, route, submit,
persist, or automate anything.

The narrow purpose is:

- convert a deterministic Candidate 1 `ReviewReport` into a deterministic manual
  decision packet
- carry forward review readiness, missing evidence, recommended checks, and
  inspection focus
- assign one bounded manual disposition
- record explicit reasons and required follow-up for human inspection

Candidate 2 is not a control plane. It is a typed review artifact layer.

## Why Candidate 2 Belongs After Candidate 1

Candidate 1 established the evidence chain:

1. raw future-system records
2. review packets
3. evidence judgments
4. deficiency summaries
5. recommendations
6. bundles
7. reports
8. replay scenarios

Candidate 2 belongs after that because manual gate packets should not inspect raw
future-system records directly. They should consume the already-normalized Candidate
1 review report shape and add only a bounded manual disposition layer.

This keeps review/replay evidence separate from manual gate disposition.

## Manual Dispositions

Candidate 2 may define these bounded dispositions:

- `hold`
- `needs_more_evidence`
- `ready_for_manual_approval`
- `rejected_for_scope`

Interpretation:

- `hold`: the report is not ready for manual approval, but the input is still inside
  Candidate 2's supported scope
- `needs_more_evidence`: the report is missing required evidence or packet components
  that must be collected or reviewed before any manual approval discussion
- `ready_for_manual_approval`: the report is review-ready and may be inspected by a
  human; this is not an automated approval
- `rejected_for_scope`: the input cannot be handled by this manual gate candidate
  without widening scope

Every disposition must include deterministic reasons and required follow-up fields.

## Deterministic Evaluation Rules

The first code phase should keep the rules intentionally small:

- if the source report is outside the supported Candidate 1 `ReviewReport` surface,
  produce `rejected_for_scope`
- if `missing_components` is non-empty, produce `needs_more_evidence`
- if `manual_review_required` is true, produce `hold`
- if `review_ready` is false, produce `hold`
- otherwise produce `ready_for_manual_approval`

The rules must preserve:

- `packet_id`
- `correlation_id`
- `review_ready`
- `manual_review_required`
- `missing_components`
- `recommended_checks`
- `final_inspection_focus`
- human-readable reasons
- required follow-up

These rules must not introduce scoring, ranking, promotion logic, or workflow
automation.

## Minimum Likely File Touch Set For Phase 15B

Phase 15B should be the first code phase for Candidate 2.

Minimum likely file touch set:

```text
src/future_system/manual_gate/__init__.py
src/future_system/manual_gate/packets.py
tests/future_system/test_manual_gate_packets.py
docs/PHASE_15B_IMPLEMENTATION_LOG.md
```

Preferred responsibilities:

- `src/future_system/manual_gate/packets.py`
  - define a manual disposition enum
  - define a manual decision packet model
  - define a pure in-memory function that consumes `ReviewReport`
  - return deterministic reasons and required follow-up
- `tests/future_system/test_manual_gate_packets.py`
  - prove the four dispositions from deterministic in-memory report fixtures
  - prove reasons and required follow-up are explicit
  - prove no imports from `polymarket_arb`
  - prove no live, venue, auth, credential, signing, order, submit, or position
    semantics are introduced
- `docs/PHASE_15B_IMPLEMENTATION_LOG.md`
  - record files created
  - record exported models/functions
  - record validation results
  - record boundaries and deferred items

No existing Candidate 1 review modules should be modified in Phase 15B unless the
manual gate cannot consume the current `ReviewReport` shape without a documented
contradiction. If that happens, Phase 15B must stop and ask for reauthorization
instead of widening.

## Explicit Non-Goals

Candidate 2 must not:

- modify any file under `src/polymarket_arb/`
- add routes
- add CLI commands
- add network calls
- add database connections
- add filesystem writes in code
- add adapters
- add execution logic
- add reconciliation logic
- add portfolio or capital-allocation logic
- add governance enforcement
- add auth, secrets, credentials, private keys, or signing
- add venue-facing semantics
- add approval automation
- add promotion automation
- add live gating
- add background tasks
- redefine Candidate 1 history
- widen into a broad control plane

Candidate 2 may produce manual gate packets only. Those packets are inspection
artifacts, not actions.

## Validation Expectations For Phase 15B

Phase 15B must run and pass:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
python -m pytest tests/future_system/test_manual_gate_packets.py -v
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
python -m pytest tests/future_system/ -v
```

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
make validate
```

Phase 15B should also inspect the final file touch set before commit:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
git status -sb
git diff --name-only HEAD
```

## Halt Conditions

Candidate 2 implementation must halt immediately if:

- any file under `src/polymarket_arb/` would need to change
- a route, CLI command, adapter, network call, database connection, or filesystem
  write becomes necessary
- the manual gate needs to perform automated approval, promotion, escalation, or
  runtime action
- the implementation requires auth, secrets, keys, signing, order semantics,
  venue-facing semantics, or position semantics
- the design starts requiring reconciliation, portfolio, governance enforcement, or
  broad control-plane behavior
- the first code phase cannot consume Candidate 1 `ReviewReport` outputs without
  changing Candidate 1 review semantics
- the file touch set starts expanding beyond the narrow manual gate packet layer

A halt means: stop, do not commit, report the conflict, and request supervisor and
reviewer reauthorization.

## Phase 15A Outcome

Phase 15A defines Candidate 2 only.

It does not begin implementation. It does not select broader vNext work. It does not
change Candidate 1 or the frozen baseline.
