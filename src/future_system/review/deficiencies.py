"""Deterministic deficiency summaries for future-system review evidence."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId
from future_system.review.evidence import EvidenceStatus, ReviewPacketEvidence
from future_system.review.packets import PacketMissingComponent


class DeficiencyCategory(str, Enum):
    """Bounded deficiency category derived from review-packet evidence."""

    COMPLETENESS = "completeness"
    ATTRIBUTION = "attribution"
    TRACEABILITY = "traceability"
    MIXED = "mixed"
    NONE = "none"


class DeficiencySummary(BaseModel):
    """Pure in-memory deficiency summary for one review packet evidence judgment."""

    packet_id: str
    correlation_id: CorrelationId
    evidence_status: EvidenceStatus
    headline: str
    findings: list[str]
    missing_components: list[PacketMissingComponent]
    deficiency_category: DeficiencyCategory
    inspection_focus: str
    review_ready: bool


def summarize_deficiencies(evidence: ReviewPacketEvidence) -> DeficiencySummary:
    """Produce a deterministic deficiency summary from review-packet evidence."""

    deficiency_category = _deficiency_category(evidence)
    headline = _headline(evidence, deficiency_category)
    findings = _findings(evidence, deficiency_category)
    inspection_focus = _inspection_focus(evidence, deficiency_category)

    return DeficiencySummary(
        packet_id=evidence.packet_id,
        correlation_id=evidence.correlation_id,
        evidence_status=evidence.evidence_status,
        headline=headline,
        findings=findings,
        missing_components=list(evidence.missing_components),
        deficiency_category=deficiency_category,
        inspection_focus=inspection_focus,
        review_ready=evidence.review_ready,
    )


def _deficiency_category(evidence: ReviewPacketEvidence) -> DeficiencyCategory:
    if evidence.review_ready:
        return DeficiencyCategory.NONE

    has_completeness = evidence.evidence_status is EvidenceStatus.INCOMPLETE
    has_attribution = not evidence.attribution_complete
    has_traceability = not evidence.traceability_complete

    # INCOMPLETE status always categorizes as COMPLETENESS. Attribution and
    # traceability failures on an incomplete packet are artifacts of the missing
    # components — those boundaries cannot be fully evaluated until the packet has
    # all required components present.
    if has_completeness:
        return DeficiencyCategory.COMPLETENESS

    if has_attribution and has_traceability:
        return DeficiencyCategory.MIXED
    if has_attribution:
        return DeficiencyCategory.ATTRIBUTION
    if has_traceability:
        return DeficiencyCategory.TRACEABILITY

    return DeficiencyCategory.NONE


def _headline(
    evidence: ReviewPacketEvidence,
    deficiency_category: DeficiencyCategory,
) -> str:
    if deficiency_category is DeficiencyCategory.NONE:
        return (
            f"Packet {evidence.packet_id} is review-ready; "
            "no deficiencies detected."
        )
    if deficiency_category is DeficiencyCategory.COMPLETENESS:
        component_names = ", ".join(c.value for c in evidence.missing_components)
        return (
            f"Packet {evidence.packet_id} is not review-ready; "
            f"missing required components: {component_names}."
        )
    if deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return (
            f"Packet {evidence.packet_id} is not review-ready; "
            "attribution boundary failed."
        )
    if deficiency_category is DeficiencyCategory.TRACEABILITY:
        return (
            f"Packet {evidence.packet_id} is not review-ready; "
            "traceability boundary failed."
        )
    # MIXED
    return (
        f"Packet {evidence.packet_id} is not review-ready; "
        "multiple deficiency boundaries failed."
    )


def _findings(
    evidence: ReviewPacketEvidence,
    deficiency_category: DeficiencyCategory,
) -> list[str]:
    findings: list[str] = []

    if deficiency_category is DeficiencyCategory.NONE:
        findings.append("All required packet boundaries are satisfied.")
        findings.append("Attribution is complete.")
        findings.append("Traceability is complete.")
        return findings

    for reason in evidence.reasons:
        if reason == "packet_incomplete":
            findings.append("Packet is incomplete; required components are absent.")
        elif reason.startswith("missing_component:"):
            component = reason[len("missing_component:"):]
            findings.append(f"Required component absent: {component}.")
        elif reason == "attribution_incomplete":
            findings.append(
                "Attribution boundary failed: one or more records lack required "
                "actor, action, granted_by, or rationale fields."
            )
        elif reason == "traceability_incomplete":
            findings.append(
                "Traceability boundary failed: correlation coverage, trace ordering, "
                "or audit-trace membership is broken."
            )

    return findings


def _inspection_focus(
    evidence: ReviewPacketEvidence,
    deficiency_category: DeficiencyCategory,
) -> str:
    if deficiency_category is DeficiencyCategory.NONE:
        return "No further inspection required; packet is review-ready."

    if deficiency_category is DeficiencyCategory.COMPLETENESS:
        component_names = ", ".join(c.value for c in evidence.missing_components)
        return f"Inspect missing components: {component_names}."

    if deficiency_category is DeficiencyCategory.ATTRIBUTION:
        return (
            "Inspect event attributed_to fields and audit record actor, action, "
            "granted_by, and rationale fields."
        )

    if deficiency_category is DeficiencyCategory.TRACEABILITY:
        return (
            "Inspect correlation_id consistency across events, audit records, and "
            "trace links; verify trace ordering and audit-trace membership."
        )

    # MIXED — list the active deficiency types in a stable order
    parts: list[str] = []
    if evidence.evidence_status is EvidenceStatus.INCOMPLETE:
        component_names = ", ".join(c.value for c in evidence.missing_components)
        parts.append(f"missing components ({component_names})")
    if not evidence.attribution_complete:
        parts.append("attribution fields")
    if not evidence.traceability_complete:
        parts.append("traceability coverage")
    return f"Inspect: {'; '.join(parts)}."
