"""Deterministic in-memory rendering for manual gate comparison replay reports."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.comparison_replay import ManualGateComparisonReplayResult
from future_system.observability.correlation import CorrelationId


class ManualGateComparisonReplayReport(BaseModel):
    """Pure in-memory human-readable report for one replay result."""

    scenario_name: str
    left_packet_id: str
    right_packet_id: str
    left_correlation_id: CorrelationId
    right_correlation_id: CorrelationId
    report_headline: str
    replay_summary: str
    changed_fields: list[str]
    bundles_equal: bool


def render_manual_gate_comparison_replay_report(
    replay_result: ManualGateComparisonReplayResult,
) -> ManualGateComparisonReplayReport:
    """Render one deterministic report from one replay result artifact."""

    changed_fields = list(replay_result.changed_fields)
    bundles_equal = replay_result.bundles_equal

    if bundles_equal:
        report_headline = "Manual gate comparison replay has no bounded differences."
        replay_summary = (
            f"Replay scenario '{replay_result.scenario_name}' produced no bounded "
            "differences."
        )
    else:
        report_headline = (
            "Manual gate comparison replay has bounded field differences."
        )
        changed_text = ", ".join(changed_fields)
        replay_summary = (
            f"Replay scenario '{replay_result.scenario_name}' produced bounded "
            f"differences in: {changed_text}."
        )

    return ManualGateComparisonReplayReport(
        scenario_name=replay_result.scenario_name,
        left_packet_id=replay_result.comparison.left_packet_id,
        right_packet_id=replay_result.comparison.right_packet_id,
        left_correlation_id=replay_result.comparison.left_correlation_id,
        right_correlation_id=replay_result.comparison.right_correlation_id,
        report_headline=report_headline,
        replay_summary=replay_summary,
        changed_fields=changed_fields,
        bundles_equal=bundles_equal,
    )
