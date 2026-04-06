"""Deterministic in-memory review packets for future-system records."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from future_system.observability.audit import AuditRecord
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import FutureSystemEvent


class PacketCompletenessStatus(str, Enum):
    """Completeness state for a review packet."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class PacketMissingComponent(str, Enum):
    """Required packet components that may be missing."""

    EVENTS = "events"
    AUDIT_RECORDS = "audit_records"
    ORDERED_TRACE = "ordered_trace"


class ReviewPacketScope(str, Enum):
    """Scope summary for a packet."""

    DECISION = RecordScope.DECISION.value
    CONTROL = RecordScope.CONTROL.value
    RECOVERY = RecordScope.RECOVERY.value
    GOVERNANCE = RecordScope.GOVERNANCE.value
    MIXED = "mixed"


class FutureSystemReviewPacket(BaseModel):
    """Deterministic in-memory review packet for one correlation group."""

    packet_id: str
    correlation_id: CorrelationId
    record_scope: ReviewPacketScope
    events: list[FutureSystemEvent]
    audit_records: list[AuditRecord]
    ordered_trace: list[TraceLink]
    completeness_status: PacketCompletenessStatus
    missing_components: list[PacketMissingComponent]
    summary_text: str


@dataclass
class _PacketGroup:
    """Internal collection bucket for one correlation group."""

    events: list[FutureSystemEvent] = field(default_factory=list)
    audit_records: list[AuditRecord] = field(default_factory=list)
    trace_links: list[TraceLink] = field(default_factory=list)


def build_review_packets(
    events: Sequence[FutureSystemEvent],
    audit_records: Sequence[AuditRecord],
    trace_links: Sequence[TraceLink],
) -> list[FutureSystemReviewPacket]:
    """Build deterministic review packets grouped by correlation identifier."""

    groups: defaultdict[str, _PacketGroup] = defaultdict(_PacketGroup)

    for event in events:
        groups[event.correlation_id.value].events.append(event)

    for record in audit_records:
        groups[record.trace.correlation_id].audit_records.append(record)

    for trace_link in trace_links:
        groups[trace_link.correlation_id].trace_links.append(trace_link)

    packets: list[FutureSystemReviewPacket] = []
    for correlation_value in sorted(groups):
        packets.append(_build_packet(correlation_value, groups[correlation_value]))
    return packets


def _build_packet(
    correlation_value: str,
    group: _PacketGroup,
) -> FutureSystemReviewPacket:
    sorted_events = sorted(
        group.events,
        key=lambda event: (
            event.occurred_at,
            event.event_id,
            event.event_kind.value,
            event.attributed_to,
        ),
    )
    sorted_audit_records = sorted(
        group.audit_records,
        key=lambda record: (
            record.decided_at,
            record.record_id,
            record.decision_kind.value,
            record.actor,
        ),
    )
    sorted_trace = _sorted_trace(group.trace_links)

    missing_components = _missing_components(
        sorted_events,
        sorted_audit_records,
        sorted_trace,
    )
    completeness_status = (
        PacketCompletenessStatus.COMPLETE
        if not missing_components
        else PacketCompletenessStatus.INCOMPLETE
    )
    record_scope = _packet_scope(sorted_events, sorted_audit_records, sorted_trace)

    return FutureSystemReviewPacket(
        packet_id=f"review-packet:{correlation_value}",
        correlation_id=CorrelationId(value=correlation_value),
        record_scope=record_scope,
        events=sorted_events,
        audit_records=sorted_audit_records,
        ordered_trace=sorted_trace,
        completeness_status=completeness_status,
        missing_components=missing_components,
        summary_text=_summary_text(
            correlation_value=correlation_value,
            completeness_status=completeness_status,
            missing_components=missing_components,
            event_count=len(sorted_events),
            audit_record_count=len(sorted_audit_records),
            trace_count=len(sorted_trace),
        ),
    )


def _sorted_trace(trace_links: Sequence[TraceLink]) -> list[TraceLink]:
    deduped: dict[tuple[str, str, int, datetime], TraceLink] = {}

    for trace_link in trace_links:
        deduped[_trace_key(trace_link)] = trace_link

    return sorted(
        deduped.values(),
        key=lambda trace_link: (
            trace_link.sequence,
            trace_link.created_at,
            trace_link.record_scope.value,
            trace_link.correlation_id,
        ),
    )


def _trace_key(trace_link: TraceLink) -> tuple[str, str, int, datetime]:
    return (
        trace_link.correlation_id,
        trace_link.record_scope.value,
        trace_link.sequence,
        trace_link.created_at,
    )


def _missing_components(
    events: Iterable[FutureSystemEvent],
    audit_records: Iterable[AuditRecord],
    ordered_trace: Iterable[TraceLink],
) -> list[PacketMissingComponent]:
    missing: list[PacketMissingComponent] = []
    if not list(events):
        missing.append(PacketMissingComponent.EVENTS)
    if not list(audit_records):
        missing.append(PacketMissingComponent.AUDIT_RECORDS)
    if not list(ordered_trace):
        missing.append(PacketMissingComponent.ORDERED_TRACE)
    return missing


def _packet_scope(
    events: Sequence[FutureSystemEvent],
    audit_records: Sequence[AuditRecord],
    ordered_trace: Sequence[TraceLink],
) -> ReviewPacketScope:
    scope_values = {
        event.record_scope.value for event in events
    } | {record.trace.record_scope.value for record in audit_records} | {
        trace_link.record_scope.value for trace_link in ordered_trace
    }

    if not scope_values:
        return ReviewPacketScope.MIXED
    if len(scope_values) == 1:
        return ReviewPacketScope(scope_values.pop())
    return ReviewPacketScope.MIXED


def _summary_text(
    correlation_value: str,
    completeness_status: PacketCompletenessStatus,
    missing_components: Sequence[PacketMissingComponent],
    event_count: int,
    audit_record_count: int,
    trace_count: int,
) -> str:
    if completeness_status is PacketCompletenessStatus.COMPLETE:
        return (
            f"Correlation {correlation_value} is complete with "
            f"{event_count} events, {audit_record_count} audit records, "
            f"and {trace_count} trace links."
        )

    missing_text = ", ".join(component.value for component in missing_components)
    return (
        f"Correlation {correlation_value} is incomplete; missing {missing_text}. "
        f"Current counts: {event_count} events, {audit_record_count} audit records, "
        f"{trace_count} trace links."
    )
