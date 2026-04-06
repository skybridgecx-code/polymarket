"""Deterministic manual gate packets for review reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId
from future_system.review.reports import ReviewReport


class ManualGateDisposition(str, Enum):
    """Bounded manual gate disposition."""

    HOLD = "hold"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    READY_FOR_MANUAL_APPROVAL = "ready_for_manual_approval"
    REJECTED_FOR_SCOPE = "rejected_for_scope"


class ManualGatePacket(BaseModel):
    """Pure in-memory manual gate packet for one review report."""

    packet_id: str
    correlation_id: CorrelationId
    disposition: ManualGateDisposition
    reasons: list[str]
    required_follow_up: list[str]
    review_ready: bool
    manual_action_required: bool


def build_manual_gate_packet(report: ReviewReport) -> ManualGatePacket:
    """Build a deterministic advisory manual gate packet from a review report."""

    disposition = _disposition(report)

    return ManualGatePacket(
        packet_id=f"manual-gate:{report.packet_id}",
        correlation_id=report.correlation_id,
        disposition=disposition,
        reasons=_reasons(report, disposition),
        required_follow_up=_required_follow_up(report, disposition),
        review_ready=report.review_ready,
        manual_action_required=disposition is not ManualGateDisposition.REJECTED_FOR_SCOPE,
    )


def _disposition(report: ReviewReport) -> ManualGateDisposition:
    if report.missing_components:
        return ManualGateDisposition.NEEDS_MORE_EVIDENCE

    if report.manual_review_required:
        return ManualGateDisposition.HOLD

    if not report.review_ready:
        return ManualGateDisposition.HOLD

    return ManualGateDisposition.READY_FOR_MANUAL_APPROVAL


def _reasons(
    report: ReviewReport,
    disposition: ManualGateDisposition,
) -> list[str]:
    if disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE:
        return [
            "missing_components_present",
            *[f"missing_component:{component.value}" for component in report.missing_components],
        ]

    if disposition is ManualGateDisposition.HOLD:
        reasons: list[str] = ["manual_review_required"]
        if not report.review_ready:
            reasons.append("review_not_ready")
        return reasons

    if disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL:
        return ["review_ready"]

    return ["unsupported_scope"]


def _required_follow_up(
    report: ReviewReport,
    disposition: ManualGateDisposition,
) -> list[str]:
    if disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE:
        follow_up = [
            f"Inspect missing component: {component.value}."
            for component in report.missing_components
        ]
        return [*follow_up, *report.recommended_checks]

    if disposition is ManualGateDisposition.HOLD:
        return [*report.recommended_checks, report.final_inspection_focus]

    if disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL:
        return [
            "Perform manual inspection before any approval decision.",
            report.final_inspection_focus,
        ]

    return ["Stop review; input is outside the manual gate scope."]
