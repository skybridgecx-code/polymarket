"""Deterministic in-memory review reports for bounded inspection."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId
from future_system.review.bundles import ReviewBundle
from future_system.review.deficiencies import DeficiencyCategory
from future_system.review.evidence import EvidenceStatus
from future_system.review.packets import PacketMissingComponent


class ReviewReport(BaseModel):
    """Pure in-memory report for one review bundle."""

    packet_id: str
    correlation_id: CorrelationId
    review_ready: bool
    report_headline: str
    readiness_summary: str
    key_findings: list[str]
    missing_components: list[PacketMissingComponent]
    recommended_checks: list[str]
    final_inspection_focus: str
    manual_review_required: bool


def render_review_report(bundle: ReviewBundle) -> ReviewReport:
    """Render a deterministic human-readable report from a review bundle."""

    _validate_bundle(bundle)

    return ReviewReport(
        packet_id=bundle.packet_id,
        correlation_id=bundle.correlation_id,
        review_ready=bundle.review_ready,
        report_headline=_report_headline(bundle),
        readiness_summary=_readiness_summary(bundle),
        key_findings=list(bundle.deficiency_summary.findings),
        missing_components=list(bundle.deficiency_summary.missing_components),
        recommended_checks=list(bundle.recommendations.recommended_checks),
        final_inspection_focus=bundle.final_inspection_focus,
        manual_review_required=bundle.manual_review_required,
    )


def _validate_bundle(bundle: ReviewBundle) -> None:
    packet_ids = {
        bundle.packet_id,
        bundle.packet.packet_id,
        bundle.evidence.packet_id,
        bundle.deficiency_summary.packet_id,
        bundle.recommendations.packet_id,
    }
    if len(packet_ids) != 1:
        raise ValueError("review_report_packet_mismatch")

    correlation_ids = {
        bundle.correlation_id.value,
        bundle.packet.correlation_id.value,
        bundle.evidence.correlation_id.value,
        bundle.deficiency_summary.correlation_id.value,
        bundle.recommendations.correlation_id.value,
    }
    if len(correlation_ids) != 1:
        raise ValueError("review_report_correlation_mismatch")

    review_ready_values = {
        bundle.review_ready,
        bundle.evidence.review_ready,
        bundle.deficiency_summary.review_ready,
        bundle.recommendations.review_ready,
    }
    if len(review_ready_values) != 1:
        raise ValueError("review_report_review_ready_mismatch")


def _report_headline(bundle: ReviewBundle) -> str:
    if bundle.review_ready:
        return f"Packet {bundle.packet_id} is ready for bounded review."

    if bundle.evidence.evidence_status is EvidenceStatus.INCOMPLETE:
        return (
            f"Packet {bundle.packet_id} is not ready for bounded review; "
            "explicit review limits apply."
        )

    return (
        f"Packet {bundle.packet_id} is not ready for bounded review; "
        "manual inspection is required."
    )


def _readiness_summary(bundle: ReviewBundle) -> str:
    if bundle.review_ready:
        return (
            "Bounded review may proceed; completeness, attribution, and "
            "traceability checks are satisfied."
        )

    if bundle.evidence.evidence_status is EvidenceStatus.INCOMPLETE:
        missing_text = ", ".join(
            component.value for component in bundle.deficiency_summary.missing_components
        )
        return (
            "Bounded review must not proceed; required packet components are "
            f"missing: {missing_text}."
        )

    if bundle.deficiency_summary.deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return (
            "Bounded review must not proceed; attribution boundaries remain "
            "incomplete."
        )

    if bundle.deficiency_summary.deficiency_category is DeficiencyCategory.TRACEABILITY:
        return (
            "Bounded review must not proceed; traceability boundaries remain "
            "incomplete."
        )

    return (
        "Bounded review must not proceed; multiple review boundaries remain "
        "incomplete."
    )
