"""Structural and deterministic checks for future-system review packets."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.packets import (
    PacketCompletenessStatus,
    PacketMissingComponent,
    ReviewPacketScope,
    build_review_packets,
)

_T0 = datetime(2025, 1, 1, 0, 0, 0)
_T1 = datetime(2025, 1, 1, 0, 1, 0)
_T2 = datetime(2025, 1, 1, 0, 2, 0)

_REVIEW_SRC = (
    Path(__file__).resolve().parent.parent.parent / "src" / "future_system" / "review"
)
_FORBIDDEN_FIELD_TERMS = frozenset(
    {"venue", "auth", "credential", "sign", "position", "submit", "private"}
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
    {"live", "venue", "auth", "credential", "signing", "position"}
)


def test_records_with_same_correlation_id_are_grouped_together() -> None:
    alpha = CorrelationId(value="alpha")
    beta = CorrelationId(value="beta")

    packets = build_review_packets(
        events=[
            _event("event-b", beta, _T1),
            _event("event-a2", alpha, _T2),
            _event("event-a1", alpha, _T1),
        ],
        audit_records=[
            _audit("audit-a", "alpha", 2, _T2),
            _audit("audit-b", "beta", 1, _T1),
        ],
        trace_links=[
            _trace("alpha", 1, _T1),
            _trace("beta", 1, _T1),
        ],
    )

    assert [packet.correlation_id.value for packet in packets] == ["alpha", "beta"]
    alpha_packet = packets[0]
    beta_packet = packets[1]

    assert [event.event_id for event in alpha_packet.events] == ["event-a1", "event-a2"]
    assert [record.record_id for record in alpha_packet.audit_records] == ["audit-a"]
    assert [event.event_id for event in beta_packet.events] == ["event-b"]
    assert [record.record_id for record in beta_packet.audit_records] == ["audit-b"]


def test_packet_ordering_is_deterministic() -> None:
    packets_a = build_review_packets(
        events=[
            _event("event-2", CorrelationId(value="alpha"), _T2),
            _event("event-1", CorrelationId(value="alpha"), _T1),
        ],
        audit_records=[
            _audit("audit-2", "alpha", 2, _T2),
            _audit("audit-1", "alpha", 1, _T1),
        ],
        trace_links=[
            _trace("alpha", 3, _T2),
            _trace("alpha", 1, _T1),
        ],
    )
    packets_b = build_review_packets(
        events=list(reversed(packets_a[0].events)),
        audit_records=list(reversed(packets_a[0].audit_records)),
        trace_links=list(reversed(packets_a[0].ordered_trace)),
    )

    assert [event.event_id for event in packets_a[0].events] == ["event-1", "event-2"]
    assert [record.record_id for record in packets_a[0].audit_records] == ["audit-1", "audit-2"]
    assert [trace.sequence for trace in packets_a[0].ordered_trace] == [1, 2, 3]
    assert packets_a[0].model_dump() == packets_b[0].model_dump()


def test_missing_components_are_detected_and_reported() -> None:
    packets = build_review_packets(
        events=[_event("event-only", CorrelationId(value="alpha"), _T1)],
        audit_records=[],
        trace_links=[],
    )

    packet = packets[0]
    assert packet.completeness_status == PacketCompletenessStatus.INCOMPLETE
    assert packet.record_scope == ReviewPacketScope.GOVERNANCE
    assert packet.missing_components == [
        PacketMissingComponent.AUDIT_RECORDS,
        PacketMissingComponent.ORDERED_TRACE,
    ]
    assert "missing audit_records, ordered_trace" in packet.summary_text


def test_review_builder_is_pure_in_memory_and_has_no_baseline_imports() -> None:
    for filename in ("__init__.py", "packets.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_review_models_introduce_no_forbidden_semantic_fields() -> None:
    from future_system.review.packets import FutureSystemReviewPacket

    for field_name in FutureSystemReviewPacket.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of FutureSystemReviewPacket"
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
        description="Approval event for future-system review.",
        attributed_to="review-actor",
    )


def _audit(record_id: str, correlation_id: str, sequence: int, decided_at: datetime) -> AuditRecord:
    return AuditRecord(
        record_id=record_id,
        actor="review-actor",
        action="approve-review-packet",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic in-memory review packet check.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
