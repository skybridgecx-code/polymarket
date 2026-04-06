"""Deterministic evidence judgments for future-system review packets."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId, TraceLink
from future_system.review.packets import (
    FutureSystemReviewPacket,
    PacketCompletenessStatus,
    PacketMissingComponent,
)


class EvidenceStatus(str, Enum):
    """Bounded evidence status for a review packet."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    INCOMPLETE = "incomplete"


class ReviewPacketEvidence(BaseModel):
    """Pure in-memory evidence judgment for one review packet."""

    packet_id: str
    correlation_id: CorrelationId
    evidence_status: EvidenceStatus
    reasons: list[str]
    missing_components: list[PacketMissingComponent]
    attribution_complete: bool
    traceability_complete: bool
    review_ready: bool


def evaluate_review_packet(packet: FutureSystemReviewPacket) -> ReviewPacketEvidence:
    """Evaluate a review packet for bounded evidence readiness."""

    reasons: list[str] = []
    missing_components = list(packet.missing_components)

    attribution_complete = _attribution_complete(packet)
    traceability_complete = _traceability_complete(packet)

    if packet.completeness_status is PacketCompletenessStatus.INCOMPLETE:
        reasons.append("packet_incomplete")
        reasons.extend(
            f"missing_component:{component.value}" for component in missing_components
        )

    if not attribution_complete:
        reasons.append("attribution_incomplete")

    if not traceability_complete:
        reasons.append("traceability_incomplete")

    evidence_status = _evidence_status(
        packet=packet,
        attribution_complete=attribution_complete,
        traceability_complete=traceability_complete,
    )

    return ReviewPacketEvidence(
        packet_id=packet.packet_id,
        correlation_id=packet.correlation_id,
        evidence_status=evidence_status,
        reasons=reasons,
        missing_components=missing_components,
        attribution_complete=attribution_complete,
        traceability_complete=traceability_complete,
        review_ready=evidence_status is EvidenceStatus.SUFFICIENT,
    )


def _evidence_status(
    packet: FutureSystemReviewPacket,
    attribution_complete: bool,
    traceability_complete: bool,
) -> EvidenceStatus:
    if packet.completeness_status is PacketCompletenessStatus.INCOMPLETE:
        return EvidenceStatus.INCOMPLETE
    if not attribution_complete or not traceability_complete:
        return EvidenceStatus.INSUFFICIENT
    return EvidenceStatus.SUFFICIENT


def _attribution_complete(packet: FutureSystemReviewPacket) -> bool:
    if not packet.events or not packet.audit_records:
        return False

    event_attribution = all(event.attributed_to.strip() for event in packet.events)
    audit_attribution = all(
        record.actor.strip()
        and record.action.strip()
        and record.granted_by.strip()
        and record.rationale.strip()
        for record in packet.audit_records
    )
    return event_attribution and audit_attribution


def _traceability_complete(packet: FutureSystemReviewPacket) -> bool:
    if not packet.ordered_trace:
        return False

    correlation_value = packet.correlation_id.value
    if any(event.correlation_id.value != correlation_value for event in packet.events):
        return False
    if any(record.trace.correlation_id != correlation_value for record in packet.audit_records):
        return False
    if any(trace.correlation_id != correlation_value for trace in packet.ordered_trace):
        return False

    sorted_trace = sorted(packet.ordered_trace, key=_trace_sort_key)
    if list(packet.ordered_trace) != sorted_trace:
        return False

    trace_keys = {_trace_identity(trace) for trace in packet.ordered_trace}
    audit_trace_keys = {_trace_identity(record.trace) for record in packet.audit_records}
    return audit_trace_keys.issubset(trace_keys)


def _trace_sort_key(trace: TraceLink) -> tuple[int, datetime, str, str]:
    return (
        trace.sequence,
        trace.created_at,
        trace.record_scope.value,
        trace.correlation_id,
    )


def _trace_identity(trace: TraceLink) -> tuple[str, str, int, datetime]:
    return (
        trace.correlation_id,
        trace.record_scope.value,
        trace.sequence,
        trace.created_at,
    )
