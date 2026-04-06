"""Structural boundary checks for the future-system observability foundation.

These tests verify that the Phase 14B implementation satisfies the
Phase 13L no-touch boundaries and Phase 14A scope lock requirements.
They are deterministic structural checks, not integration tests.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent

# Fixed timestamp for deterministic fixture instantiation.
_TIMESTAMP = datetime(2025, 1, 1, 0, 0, 0)

# Path to the observability source directory, resolved from this test file.
_OBS_SRC = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "future_system"
    / "observability"
)

# Field-name substrings that must not appear on any future-system record type.
# These correspond to the Phase 13L no-touch list.
_FORBIDDEN_FIELD_TERMS = frozenset(
    {"venue", "order", "position", "credential", "sign", "auth", "submit", "private"}
)


# ---------------------------------------------------------------------------
# Check 1: all event types carry a required correlation key field
# ---------------------------------------------------------------------------


def test_future_system_event_carries_required_correlation_field() -> None:
    fields = FutureSystemEvent.model_fields
    assert "correlation_id" in fields, "FutureSystemEvent must have a correlation_id field"
    assert fields["correlation_id"].is_required(), "correlation_id must be required"


# ---------------------------------------------------------------------------
# Check 2: all audit records carry required attribution fields
# ---------------------------------------------------------------------------


def test_audit_record_carries_required_attribution_fields() -> None:
    fields = AuditRecord.model_fields
    required = {"actor", "action", "granted_by", "decided_at"}
    missing = required - fields.keys()
    assert not missing, f"AuditRecord is missing required attribution fields: {missing}"
    for name in required:
        assert fields[name].is_required(), f"AuditRecord.{name} must be a required field"


# ---------------------------------------------------------------------------
# Check 3: no observability module imports from polymarket_arb
# ---------------------------------------------------------------------------


def test_observability_modules_have_no_baseline_imports() -> None:
    for filename in ("correlation.py", "audit.py", "events.py"):
        source = (_OBS_SRC / filename).read_text()
        assert "polymarket_arb" not in source, (
            f"Forbidden baseline import found in {filename}"
        )


# ---------------------------------------------------------------------------
# Check 4: no forbidden field names on any record type
# ---------------------------------------------------------------------------


def test_no_forbidden_field_names_on_any_record_type() -> None:
    # Split on underscores so that "authority" (governance authority) is not
    # matched by the term "auth" (authentication flow).  A forbidden term must
    # appear as a complete word-part of the field name to trigger a failure.
    model_classes = [FutureSystemEvent, AuditRecord, CorrelationId, TraceLink]
    for model_class in model_classes:
        for field_name in model_class.model_fields:
            parts = set(field_name.lower().split("_"))
            matched = parts & _FORBIDDEN_FIELD_TERMS
            assert not matched, (
                f"Forbidden term(s) {matched} found in field "
                f"'{field_name}' of {model_class.__name__}"
            )


# ---------------------------------------------------------------------------
# Check 5: all record types instantiable from pure in-memory fixtures
# ---------------------------------------------------------------------------


def test_all_record_types_instantiable_from_in_memory_fixtures() -> None:
    corr_id = CorrelationId(value="test-correlation-id")
    assert corr_id.value == "test-correlation-id"

    trace = TraceLink(
        correlation_id="test-correlation-id",
        record_scope=RecordScope.DECISION,
        sequence=1,
        created_at=_TIMESTAMP,
    )
    assert trace.record_scope == RecordScope.DECISION
    assert trace.sequence == 1

    event = FutureSystemEvent(
        event_id="test-event-id",
        correlation_id=corr_id,
        event_kind=EventKind.APPROVAL_REQUESTED,
        record_scope=RecordScope.GOVERNANCE,
        occurred_at=_TIMESTAMP,
        description="Governance approval was requested for a control action.",
        attributed_to="test-actor",
    )
    assert event.event_id == "test-event-id"
    assert event.correlation_id.value == "test-correlation-id"
    assert event.attributed_to == "test-actor"

    record = AuditRecord(
        record_id="test-record-id",
        actor="test-actor",
        action="approved-control-action",
        granted_by="governance-role",
        decided_at=_TIMESTAMP,
        trace=trace,
        decision_kind=DecisionKind.APPROVAL,
        rationale="Approved under the designated governance role.",
    )
    assert record.actor == "test-actor"
    assert record.granted_by == "governance-role"
    assert record.decided_at == _TIMESTAMP
    assert record.trace.correlation_id == "test-correlation-id"
