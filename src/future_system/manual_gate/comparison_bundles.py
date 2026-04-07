"""Deterministic in-memory bundles for manual gate comparison artifacts."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.comparison_reports import ManualGateComparisonReport
from future_system.manual_gate.comparisons import ManualGateComparison
from future_system.observability.correlation import CorrelationId


class ManualGateComparisonBundle(BaseModel):
    """Pure in-memory bundle for one comparison/report pair."""

    left_packet_id: str
    right_packet_id: str
    left_correlation_id: CorrelationId
    right_correlation_id: CorrelationId
    bundle_headline: str
    comparison: ManualGateComparison
    report: ManualGateComparisonReport
    bundles_equal: bool


def format_manual_gate_comparison_bundle(
    comparison: ManualGateComparison,
    report: ManualGateComparisonReport,
) -> ManualGateComparisonBundle:
    """Assemble a deterministic bundle from comparison/report artifacts."""

    _validate_alignment(comparison, report)

    return ManualGateComparisonBundle(
        left_packet_id=comparison.left_packet_id,
        right_packet_id=comparison.right_packet_id,
        left_correlation_id=comparison.left_correlation_id,
        right_correlation_id=comparison.right_correlation_id,
        bundle_headline=_bundle_headline(comparison.bundles_equal),
        comparison=comparison,
        report=report,
        bundles_equal=comparison.bundles_equal,
    )


def _validate_alignment(
    comparison: ManualGateComparison,
    report: ManualGateComparisonReport,
) -> None:
    if comparison.left_packet_id != report.left_packet_id:
        raise ValueError("manual_gate_comparison_bundle_left_packet_mismatch")

    if comparison.right_packet_id != report.right_packet_id:
        raise ValueError("manual_gate_comparison_bundle_right_packet_mismatch")

    if comparison.left_correlation_id.value != report.left_correlation_id.value:
        raise ValueError("manual_gate_comparison_bundle_left_correlation_mismatch")

    if comparison.right_correlation_id.value != report.right_correlation_id.value:
        raise ValueError("manual_gate_comparison_bundle_right_correlation_mismatch")

    if comparison.bundles_equal is not report.bundles_equal:
        raise ValueError("manual_gate_comparison_bundle_bundles_equal_mismatch")


def _bundle_headline(bundles_equal: bool) -> str:
    if bundles_equal:
        return "Manual gate comparison bundle is aligned with no bounded differences."

    return "Manual gate comparison bundle is aligned with bounded differences."
