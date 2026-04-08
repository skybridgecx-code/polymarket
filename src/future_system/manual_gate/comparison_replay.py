"""Deterministic in-memory replay for manual gate comparison scenarios."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.bundles import ManualGateBundle
from future_system.manual_gate.comparison_bundles import (
    ManualGateComparisonBundle,
    format_manual_gate_comparison_bundle,
)
from future_system.manual_gate.comparison_reports import (
    ManualGateComparisonReport,
    render_manual_gate_comparison_report,
)
from future_system.manual_gate.comparisons import (
    ManualGateComparison,
    compare_manual_gate_bundles,
)


class ManualGateComparisonReplayScenario(BaseModel):
    """Typed single-scenario replay input for bounded comparison artifacts."""

    scenario_name: str
    left_bundle: ManualGateBundle
    right_bundle: ManualGateBundle
    expected_bundles_equal: bool
    expected_changed_fields: list[str]


class ManualGateComparisonReplayResult(BaseModel):
    """Deterministic replay output over one bounded comparison scenario."""

    scenario_name: str
    comparison: ManualGateComparison
    report: ManualGateComparisonReport
    comparison_bundle: ManualGateComparisonBundle
    bundles_equal: bool
    changed_fields: list[str]


def run_manual_gate_comparison_replay(
    scenario: ManualGateComparisonReplayScenario,
) -> ManualGateComparisonReplayResult:
    """Replay one bounded comparison scenario using existing comparison surfaces."""

    comparison = compare_manual_gate_bundles(
        scenario.left_bundle,
        scenario.right_bundle,
    )
    report = render_manual_gate_comparison_report(comparison)
    comparison_bundle = format_manual_gate_comparison_bundle(comparison, report)

    return ManualGateComparisonReplayResult(
        scenario_name=scenario.scenario_name,
        comparison=comparison,
        report=report,
        comparison_bundle=comparison_bundle,
        bundles_equal=comparison_bundle.bundles_equal,
        changed_fields=list(report.changed_fields),
    )
