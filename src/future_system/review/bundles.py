"""Deterministic in-memory review bundles for operator inspection."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId
from future_system.review.deficiencies import DeficiencyCategory, DeficiencySummary
from future_system.review.evidence import EvidenceStatus, ReviewPacketEvidence
from future_system.review.packets import FutureSystemReviewPacket
from future_system.review.recommendations import ReviewRecommendation


class ReviewBundle(BaseModel):
    """Pure in-memory bundle for one review chain."""

    packet_id: str
    correlation_id: CorrelationId
    review_ready: bool
    bundle_headline: str
    packet: FutureSystemReviewPacket
    evidence: ReviewPacketEvidence
    deficiency_summary: DeficiencySummary
    recommendations: ReviewRecommendation
    final_inspection_focus: str
    manual_review_required: bool


def format_review_bundle(
    packet: FutureSystemReviewPacket,
    evidence: ReviewPacketEvidence,
    deficiency_summary: DeficiencySummary,
    recommendations: ReviewRecommendation,
) -> ReviewBundle:
    """Assemble a deterministic operator-facing review bundle."""

    _validate_alignment(packet, evidence, deficiency_summary, recommendations)

    return ReviewBundle(
        packet_id=packet.packet_id,
        correlation_id=packet.correlation_id,
        review_ready=recommendations.review_ready,
        bundle_headline=_bundle_headline(packet.packet_id, evidence.evidence_status),
        packet=packet,
        evidence=evidence,
        deficiency_summary=deficiency_summary,
        recommendations=recommendations,
        final_inspection_focus=recommendations.inspection_focus,
        manual_review_required=recommendations.manual_review_required,
    )


def _validate_alignment(
    packet: FutureSystemReviewPacket,
    evidence: ReviewPacketEvidence,
    deficiency_summary: DeficiencySummary,
    recommendations: ReviewRecommendation,
) -> None:
    packet_ids = {
        packet.packet_id,
        evidence.packet_id,
        deficiency_summary.packet_id,
        recommendations.packet_id,
    }
    if len(packet_ids) != 1:
        raise ValueError("review_bundle_packet_mismatch")

    correlation_ids = {
        packet.correlation_id.value,
        evidence.correlation_id.value,
        deficiency_summary.correlation_id.value,
        recommendations.correlation_id.value,
    }
    if len(correlation_ids) != 1:
        raise ValueError("review_bundle_correlation_mismatch")

    review_ready_values = {
        evidence.review_ready,
        deficiency_summary.review_ready,
        recommendations.review_ready,
    }
    if len(review_ready_values) != 1:
        raise ValueError("review_bundle_review_ready_mismatch")


def _bundle_headline(packet_id: str, evidence_status: EvidenceStatus) -> str:
    if evidence_status is EvidenceStatus.SUFFICIENT:
        return f"Packet {packet_id} is bundled for bounded review."

    if evidence_status is EvidenceStatus.INCOMPLETE:
        return (
            f"Packet {packet_id} is bundled with explicit review limits; "
            "missing components prevent bounded review."
        )

    deficiency_category = DeficiencyCategory.MIXED
    if evidence_status is EvidenceStatus.INSUFFICIENT:
        deficiency_category = DeficiencyCategory.MIXED

    if deficiency_category is DeficiencyCategory.MIXED:
        return (
            f"Packet {packet_id} is bundled with explicit review limits; "
            "manual inspection is required before bounded review."
        )

    raise ValueError("review_bundle_evidence_status_unrecognized")
