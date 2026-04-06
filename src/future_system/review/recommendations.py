"""Deterministic in-memory recommendations for review deficiency summaries."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId
from future_system.review.deficiencies import DeficiencyCategory, DeficiencySummary
from future_system.review.evidence import EvidenceStatus


class ReviewRecommendation(BaseModel):
    """Pure in-memory inspection guidance for one deficiency summary."""

    packet_id: str
    correlation_id: CorrelationId
    evidence_status: EvidenceStatus
    deficiency_category: DeficiencyCategory
    review_ready: bool
    recommendation_headline: str
    recommended_checks: list[str]
    inspection_focus: str
    manual_review_required: bool


def recommend_review_steps(summary: DeficiencySummary) -> ReviewRecommendation:
    """Produce deterministic inspection guidance from a deficiency summary."""

    recommendation_headline = _headline(summary)
    recommended_checks = _recommended_checks(summary)
    inspection_focus = _inspection_focus(summary)
    manual_review_required = not summary.review_ready

    return ReviewRecommendation(
        packet_id=summary.packet_id,
        correlation_id=summary.correlation_id,
        evidence_status=summary.evidence_status,
        deficiency_category=summary.deficiency_category,
        review_ready=summary.review_ready,
        recommendation_headline=recommendation_headline,
        recommended_checks=recommended_checks,
        inspection_focus=inspection_focus,
        manual_review_required=manual_review_required,
    )


def _headline(summary: DeficiencySummary) -> str:
    if summary.deficiency_category is DeficiencyCategory.NONE:
        return (
            f"Packet {summary.packet_id} is ready for bounded review; "
            "use minimal inspection only."
        )
    if summary.deficiency_category is DeficiencyCategory.COMPLETENESS:
        return (
            f"Packet {summary.packet_id} requires missing-component inspection "
            "before bounded review."
        )
    if summary.deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return (
            f"Packet {summary.packet_id} requires attribution-trail inspection "
            "before bounded review."
        )
    if summary.deficiency_category is DeficiencyCategory.TRACEABILITY:
        return (
            f"Packet {summary.packet_id} requires trace-consistency inspection "
            "before bounded review."
        )
    return (
        f"Packet {summary.packet_id} requires combined deficiency inspection "
        "before bounded review."
    )


def _recommended_checks(summary: DeficiencySummary) -> list[str]:
    if summary.deficiency_category is DeficiencyCategory.NONE:
        return ["Confirm the packet contents stay unchanged during bounded review."]

    if summary.deficiency_category is DeficiencyCategory.COMPLETENESS:
        return _completeness_checks(summary)

    if summary.deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return [
            "Inspect event attribution fields for missing or blank values.",
            "Inspect audit actor, action, granted_by, and rationale fields.",
        ]

    if summary.deficiency_category is DeficiencyCategory.TRACEABILITY:
        return [
            "Inspect correlation_id consistency across packet records.",
            "Inspect trace sequence continuity and audit-trace membership.",
        ]

    checks: list[str] = [
        "Inspect event attribution fields for missing or blank values.",
        "Inspect audit actor, action, granted_by, and rationale fields.",
        "Inspect correlation_id consistency across packet records.",
        "Inspect trace sequence continuity and audit-trace membership.",
    ]
    return checks


def _completeness_checks(summary: DeficiencySummary) -> list[str]:
    checks: list[str] = []
    for component in summary.missing_components:
        if component.value == "events":
            checks.append("Inspect the packet for absent event records.")
        elif component.value == "audit_records":
            checks.append("Inspect the packet for absent audit records.")
        elif component.value == "ordered_trace":
            checks.append("Inspect the packet for absent trace links.")
    return checks


def _inspection_focus(summary: DeficiencySummary) -> str:
    if summary.deficiency_category is DeficiencyCategory.NONE:
        return "Minimal bounded review confirmation only."
    if summary.deficiency_category is DeficiencyCategory.COMPLETENESS:
        return "Inspect absent packet components before any further review."
    if summary.deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return "Inspect attribution trail consistency across event and audit records."
    if summary.deficiency_category is DeficiencyCategory.TRACEABILITY:
        return "Inspect trace consistency across packet correlations and trace links."
    return "Inspect attribution trail first, then inspect trace consistency."
