"""Deterministic in-memory manual gate reports for bounded inspection."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.packets import ManualGateDisposition, ManualGatePacket
from future_system.observability.correlation import CorrelationId


class ManualGateReport(BaseModel):
    """Pure in-memory report for one manual gate packet."""

    packet_id: str
    correlation_id: CorrelationId
    disposition: ManualGateDisposition
    report_headline: str
    decision_summary: str
    key_reasons: list[str]
    required_follow_up: list[str]
    review_ready: bool
    manual_action_required: bool


def render_manual_gate_report(packet: ManualGatePacket) -> ManualGateReport:
    """Render a deterministic human-readable report from a manual gate packet."""

    return ManualGateReport(
        packet_id=packet.packet_id,
        correlation_id=packet.correlation_id,
        disposition=packet.disposition,
        report_headline=_report_headline(packet),
        decision_summary=_decision_summary(packet),
        key_reasons=list(packet.reasons),
        required_follow_up=list(packet.required_follow_up),
        review_ready=packet.review_ready,
        manual_action_required=packet.manual_action_required,
    )


def _report_headline(packet: ManualGatePacket) -> str:
    if packet.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL:
        return f"Manual gate packet {packet.packet_id} is ready for manual approval review."

    if packet.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE:
        return (
            f"Manual gate packet {packet.packet_id} needs more evidence "
            "before manual approval review."
        )

    if packet.disposition is ManualGateDisposition.HOLD:
        return f"Manual gate packet {packet.packet_id} is on hold for manual review."

    return f"Manual gate packet {packet.packet_id} is rejected for current scope."


def _decision_summary(packet: ManualGatePacket) -> str:
    if packet.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL:
        return (
            "Manual gate review may proceed with human inspection; "
            "the packet is review-ready."
        )

    if packet.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE:
        return (
            "Manual gate review must pause until missing evidence "
            "is supplied for inspection."
        )

    if packet.disposition is ManualGateDisposition.HOLD:
        if not packet.review_ready:
            return (
                "Manual gate review remains on hold because the "
                "source review is not ready."
            )
        return "Manual gate review remains on hold pending additional human inspection."

    return "Manual gate review cannot proceed because input is outside bounded scope."
