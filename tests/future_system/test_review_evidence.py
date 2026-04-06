"""Structural and deterministic checks for review-packet evidence judgments."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.evidence import (
    EvidenceStatus,
    ReviewPacketEvidence,
    evaluate_review_packet,
)
from future_system.review.packets import build_review_packets

_T1 = datetime(2025, 1, 1, 0, 1, 0)
_T2 = datetime(2025, 1, 1, 0, 2, 0)

_REVIEW_SRC = (
    Path(__file__).resolve().parent.parent.parent / "src" / "future_system" / "review"
)
_FORBIDDEN_FIELD_TERMS = frozenset(
    {
        "venue",
        "auth",
        "credential",
        "sign",
        "position",
        "submit",
        "private",
        "order",
        "live",
    }
)
_FORBIDDEN_IO_TERMS = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "sqlite",
    "psycopg",
    "open(",
    "write_text(",
    "write_bytes(",
)
_FORBIDDEN_SOURCE_WORDS = frozenset(
    {"venue", "auth", "credential", "signing", "position", "submit", "live"}
)


def test_complete_packets_evaluate_deterministically() -> None:
    packet = build_review_packets(
        events=[_event("event-a", CorrelationId(value="alpha"), _T1)],
        audit_records=[_audit("audit-a", "alpha", 1, _T1)],
        trace_links=[_trace("alpha", 1, _T1), _trace("alpha", 2, _T2)],
    )[0]

    evaluation_a = evaluate_review_packet(packet)
    evaluation_b = evaluate_review_packet(packet)

    assert evaluation_a.model_dump() == evaluation_b.model_dump()
    assert evaluation_a.evidence_status == EvidenceStatus.SUFFICIENT
    assert evaluation_a.attribution_complete is True
    assert evaluation_a.traceability_complete is True
    assert evaluation_a.review_ready is True
    assert evaluation_a.reasons == []


def test_incomplete_packets_are_labeled_correctly() -> None:
    packet = build_review_packets(
        events=[_event("event-only", CorrelationId(value="alpha"), _T1)],
        audit_records=[],
        trace_links=[],
    )[0]

    evaluation = evaluate_review_packet(packet)

    assert evaluation.evidence_status == EvidenceStatus.INCOMPLETE
    assert evaluation.attribution_complete is False
    assert evaluation.traceability_complete is False
    assert evaluation.review_ready is False
    assert evaluation.missing_components == packet.missing_components
    assert "packet_incomplete" in evaluation.reasons


def test_missing_components_propagate_clearly() -> None:
    packet = build_review_packets(
        events=[],
        audit_records=[_audit("audit-only", "alpha", 1, _T1)],
        trace_links=[],
    )[0]

    evaluation = evaluate_review_packet(packet)

    assert evaluation.missing_components == packet.missing_components
    assert "missing_component:events" in evaluation.reasons
    assert "missing_component:ordered_trace" not in evaluation.reasons
    assert evaluation.traceability_complete is True


def test_complete_packet_with_broken_attribution_is_insufficient() -> None:
    packet = build_review_packets(
        events=[_event("event-a", CorrelationId(value="alpha"), _T1)],
        audit_records=[_audit("audit-a", "alpha", 1, _T1)],
        trace_links=[_trace("alpha", 1, _T1)],
    )[0]
    broken_packet = packet.model_copy(
        update={
            "events": [
                packet.events[0].model_copy(update={"attributed_to": ""}),
            ]
        }
    )

    evaluation = evaluate_review_packet(broken_packet)

    assert evaluation.evidence_status == EvidenceStatus.INSUFFICIENT
    assert evaluation.attribution_complete is False
    assert evaluation.traceability_complete is True
    assert evaluation.review_ready is False
    assert evaluation.reasons == ["attribution_incomplete"]


def test_evaluator_output_is_pure_in_memory_only_and_has_no_baseline_imports() -> None:
    for filename in ("__init__.py", "evidence.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_evaluator_model_introduces_no_forbidden_semantic_fields() -> None:
    for field_name in ReviewPacketEvidence.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ReviewPacketEvidence"
        )


def _event(
    event_id: str,
    correlation_id: CorrelationId,
    occurred_at: datetime,
) -> FutureSystemEvent:
    return FutureSystemEvent(
        event_id=event_id,
        correlation_id=correlation_id,
        event_kind=EventKind.APPROVAL_GRANTED,
        record_scope=RecordScope.GOVERNANCE,
        occurred_at=occurred_at,
        description="Review evidence event.",
        attributed_to="review-actor",
    )


def _audit(record_id: str, correlation_id: str, sequence: int, decided_at: datetime) -> AuditRecord:
    return AuditRecord(
        record_id=record_id,
        actor="review-actor",
        action="assess-review-readiness",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic evidence evaluation check.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
