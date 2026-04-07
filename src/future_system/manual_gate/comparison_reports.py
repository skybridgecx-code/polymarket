"""Deterministic in-memory render layer for manual gate comparisons."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.comparisons import ManualGateComparison
from future_system.observability.correlation import CorrelationId


class ManualGateComparisonReport(BaseModel):
    """Pure in-memory human-readable report for one manual gate comparison."""

    left_packet_id: str
    right_packet_id: str
    left_correlation_id: CorrelationId
    right_correlation_id: CorrelationId
    report_headline: str
    comparison_summary: str
    changed_fields: list[str]
    added_reasons: list[str]
    removed_reasons: list[str]
    added_required_follow_up: list[str]
    removed_required_follow_up: list[str]
    bundles_equal: bool


def render_manual_gate_comparison_report(
    comparison: ManualGateComparison,
) -> ManualGateComparisonReport:
    """Render a deterministic report from one manual gate comparison artifact."""

    changed_fields = _changed_fields(comparison)

    return ManualGateComparisonReport(
        left_packet_id=comparison.left_packet_id,
        right_packet_id=comparison.right_packet_id,
        left_correlation_id=comparison.left_correlation_id,
        right_correlation_id=comparison.right_correlation_id,
        report_headline=_report_headline(comparison),
        comparison_summary=_comparison_summary(comparison, changed_fields),
        changed_fields=changed_fields,
        added_reasons=list(comparison.added_reasons),
        removed_reasons=list(comparison.removed_reasons),
        added_required_follow_up=list(comparison.added_required_follow_up),
        removed_required_follow_up=list(comparison.removed_required_follow_up),
        bundles_equal=comparison.bundles_equal,
    )


def _changed_fields(comparison: ManualGateComparison) -> list[str]:
    changed_fields: list[str] = []

    if not comparison.same_packet_id:
        changed_fields.append("packet_id")
    if not comparison.same_correlation_id:
        changed_fields.append("correlation_id")
    if comparison.disposition_changed:
        changed_fields.append("disposition")
    if comparison.review_ready_changed:
        changed_fields.append("review_ready")
    if comparison.manual_action_required_changed:
        changed_fields.append("manual_action_required")
    if comparison.added_reasons or comparison.removed_reasons:
        changed_fields.append("reasons")
    if comparison.added_required_follow_up or comparison.removed_required_follow_up:
        changed_fields.append("required_follow_up")

    return changed_fields


def _report_headline(comparison: ManualGateComparison) -> str:
    if comparison.bundles_equal:
        return "Manual gate bundles are equivalent for bounded comparison."

    return "Manual gate bundles differ for bounded comparison."


def _comparison_summary(
    comparison: ManualGateComparison,
    changed_fields: list[str],
) -> str:
    if comparison.bundles_equal:
        return (
            "No bounded differences detected across packet, correlation, disposition, "
            "readiness, manual-action, reasons, and required follow-up fields."
        )

    changed_text = ", ".join(changed_fields)
    return f"Bounded differences detected in: {changed_text}."
