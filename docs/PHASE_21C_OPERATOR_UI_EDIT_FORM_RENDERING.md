# Phase 21C Operator UI Edit Form Rendering

## Scope

Phase 21C adds a read-only/preview edit form surface to the local `future_system` operator UI detail page.

This phase intentionally does not add POST/write behavior.

## What Changed

- Detail pages now render an **Operator Review Edit Form** section.
- Existing companion metadata pre-fills review status, operator decision, notes, and reviewer identity.
- Missing or malformed companion metadata shows a bounded unavailable state.
- The submit button is disabled until the later POST/update phase.

## Boundaries Preserved

- no DB persistence
- no queues/jobs/scheduling
- no notification/delivery/inbox workflow
- no production execution/trading behavior
- no `src/polymarket_arb/*` integration
- no operator decision write route yet

## Next Phase

Phase 21D should add the bounded POST/update route using the helper contracts from Phase 21B.
