"""Deterministic in-memory manual gate bundles for bounded inspection."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.packets import ManualGateDisposition, ManualGatePacket
from future_system.manual_gate.replay import ManualGateReplayResult
from future_system.manual_gate.reports import ManualGateReport, render_manual_gate_report
from future_system.observability.correlation import CorrelationId


class ManualGateBundle(BaseModel):
    """Pure in-memory bundle for one manual gate packet/report pair."""

    packet_id: str
    correlation_id: CorrelationId
    bundle_headline: str
    disposition: ManualGateDisposition
    packet: ManualGatePacket
    report: ManualGateReport
    review_ready: bool
    manual_action_required: bool


def format_manual_gate_bundle(
    packet: ManualGatePacket,
    report: ManualGateReport,
) -> ManualGateBundle:
    """Assemble a deterministic operator-facing manual gate bundle."""

    _validate_alignment(packet, report)

    return ManualGateBundle(
        packet_id=packet.packet_id,
        correlation_id=packet.correlation_id,
        bundle_headline=_bundle_headline(packet.packet_id, packet.disposition),
        disposition=packet.disposition,
        packet=packet,
        report=report,
        review_ready=packet.review_ready,
        manual_action_required=packet.manual_action_required,
    )


def format_manual_gate_replay_bundle(result: ManualGateReplayResult) -> ManualGateBundle:
    """Assemble a manual gate bundle from one replay result."""

    report = render_manual_gate_report(result.gate_packet)
    return format_manual_gate_bundle(result.gate_packet, report)


def _validate_alignment(packet: ManualGatePacket, report: ManualGateReport) -> None:
    if packet.packet_id != report.packet_id:
        raise ValueError("manual_gate_bundle_packet_mismatch")

    if packet.correlation_id.value != report.correlation_id.value:
        raise ValueError("manual_gate_bundle_correlation_mismatch")

    if packet.disposition is not report.disposition:
        raise ValueError("manual_gate_bundle_disposition_mismatch")

    if packet.review_ready is not report.review_ready:
        raise ValueError("manual_gate_bundle_review_ready_mismatch")

    if packet.manual_action_required is not report.manual_action_required:
        raise ValueError("manual_gate_bundle_manual_action_mismatch")


def _bundle_headline(packet_id: str, disposition: ManualGateDisposition) -> str:
    if disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL:
        return f"Manual gate packet {packet_id} is bundled for manual approval inspection."

    if disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE:
        return (
            f"Manual gate packet {packet_id} is bundled with explicit manual limits; "
            "missing evidence blocks review."
        )

    if disposition is ManualGateDisposition.HOLD:
        return f"Manual gate packet {packet_id} is bundled on hold for manual review."

    if disposition is ManualGateDisposition.REJECTED_FOR_SCOPE:
        return f"Manual gate packet {packet_id} is bundled as out of current scope."

    raise ValueError("manual_gate_bundle_disposition_unrecognized")
