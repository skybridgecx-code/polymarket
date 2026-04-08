"""Structural and deterministic checks for manual gate comparison replay."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.bundles import ManualGateBundle, format_manual_gate_bundle
from future_system.manual_gate.comparison_bundles import format_manual_gate_comparison_bundle
from future_system.manual_gate.comparison_replay import (
    ManualGateComparisonReplayResult,
    ManualGateComparisonReplayScenario,
    run_manual_gate_comparison_replay,
)
from future_system.manual_gate.comparison_reports import render_manual_gate_comparison_report
from future_system.manual_gate.comparisons import compare_manual_gate_bundles
from future_system.manual_gate.packets import build_manual_gate_packet
from future_system.manual_gate.reports import render_manual_gate_report
from future_system.observability.correlation import CorrelationId
from future_system.review.packets import PacketMissingComponent
from future_system.review.reports import ReviewReport

_MANUAL_GATE_SRC = (
    Path(__file__).resolve().parent.parent.parent / "src" / "future_system" / "manual_gate"
)
_FORBIDDEN_IO_TERMS = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "sqlite",
    "psycopg",
    "open(",
    "write_text(",
    "write_bytes(",
)
_FORBIDDEN_SOURCE_WORDS = frozenset(
    {"venue", "auth", "credential", "signing", "position", "submit", "live", "order"}
)
_FORBIDDEN_AUTOMATION_CONTROL_WORDS = frozenset(
    {
        "automation",
        "automate",
        "autonomous",
        "orchestration",
        "workflow",
        "runtime",
        "promotion",
        "promote",
        "escalation",
        "control",
        "plane",
    }
)


def test_equal_scenario_replays_deterministically() -> None:
    scenario = _scenario(
        scenario_name="equal",
        left_bundle=_bundle(correlation_value="corr-1"),
        right_bundle=_bundle(correlation_value="corr-1"),
        expected_bundles_equal=True,
        expected_changed_fields=[],
    )

    replay_a = run_manual_gate_comparison_replay(scenario)
    replay_b = run_manual_gate_comparison_replay(scenario)

    assert isinstance(replay_a, ManualGateComparisonReplayResult)
    assert replay_a.model_dump() == replay_b.model_dump()
    assert replay_a.bundles_equal is True
    assert replay_a.changed_fields == []


def test_differing_scenario_replays_deterministically() -> None:
    left = _bundle(correlation_value="corr-2")
    right = left.model_copy(
        update={
            "review_ready": False,
            "manual_action_required": False,
        }
    )
    scenario = _scenario(
        scenario_name="different",
        left_bundle=left,
        right_bundle=right,
        expected_bundles_equal=False,
        expected_changed_fields=["review_ready", "manual_action_required"],
    )

    replay_a = run_manual_gate_comparison_replay(scenario)
    replay_b = run_manual_gate_comparison_replay(scenario)

    assert replay_a.model_dump() == replay_b.model_dump()
    assert replay_a.bundles_equal is False
    assert replay_a.changed_fields == ["review_ready", "manual_action_required"]


def test_replay_result_mirrors_comparison_report_bundle_artifacts_exactly() -> None:
    left = _bundle(correlation_value="corr-3")
    right = _bundle(
        correlation_value="corr-3",
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
    )
    scenario = _scenario(
        scenario_name="mirror",
        left_bundle=left,
        right_bundle=right,
        expected_bundles_equal=False,
        expected_changed_fields=["disposition", "review_ready", "manual_action_required"],
    )

    expected_comparison = compare_manual_gate_bundles(scenario.left_bundle, scenario.right_bundle)
    expected_report = render_manual_gate_comparison_report(expected_comparison)
    expected_bundle = format_manual_gate_comparison_bundle(expected_comparison, expected_report)
    replay = run_manual_gate_comparison_replay(scenario)

    assert replay.scenario_name == scenario.scenario_name
    assert replay.comparison.model_dump() == expected_comparison.model_dump()
    assert replay.report.model_dump() == expected_report.model_dump()
    assert replay.comparison_bundle.model_dump() == expected_bundle.model_dump()


def test_replay_result_bounded_outputs_mirror_produced_artifacts() -> None:
    left = _bundle(correlation_value="corr-4")
    right = left.model_copy(update={"manual_action_required": False})
    scenario = _scenario(
        scenario_name="actual-only",
        left_bundle=left,
        right_bundle=right,
        expected_bundles_equal=True,
        expected_changed_fields=["packet_id"],
    )

    replay = run_manual_gate_comparison_replay(scenario)

    assert replay.bundles_equal is replay.comparison.bundles_equal
    assert replay.bundles_equal is replay.report.bundles_equal
    assert replay.bundles_equal is replay.comparison_bundle.bundles_equal
    assert replay.changed_fields == replay.report.changed_fields
    assert replay.changed_fields != scenario.expected_changed_fields
    assert replay.bundles_equal is not scenario.expected_bundles_equal


def test_repeated_replay_is_deterministic() -> None:
    scenario = _scenario(
        scenario_name="repeat",
        left_bundle=_bundle(correlation_value="corr-5"),
        right_bundle=_bundle(correlation_value="corr-6"),
        expected_bundles_equal=False,
        expected_changed_fields=["packet_id", "correlation_id"],
    )

    replay_a = run_manual_gate_comparison_replay(scenario)
    replay_b = run_manual_gate_comparison_replay(scenario)

    assert replay_a.model_dump() == replay_b.model_dump()


def test_typed_correlation_id_is_preserved_through_replay_output() -> None:
    scenario = _scenario(
        scenario_name="typed-correlation",
        left_bundle=_bundle(correlation_value="corr-left"),
        right_bundle=_bundle(correlation_value="corr-right"),
        expected_bundles_equal=False,
        expected_changed_fields=["packet_id", "correlation_id"],
    )

    replay = run_manual_gate_comparison_replay(scenario)

    assert isinstance(replay.comparison.left_correlation_id, CorrelationId)
    assert isinstance(replay.comparison.right_correlation_id, CorrelationId)
    assert isinstance(replay.report.left_correlation_id, CorrelationId)
    assert isinstance(replay.report.right_correlation_id, CorrelationId)
    assert isinstance(replay.comparison_bundle.left_correlation_id, CorrelationId)
    assert isinstance(replay.comparison_bundle.right_correlation_id, CorrelationId)


def test_replay_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "comparison_replay.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_no_widened_automation_control_plane_language_is_introduced() -> None:
    for filename in ("__init__.py", "comparison_replay.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_CONTROL_WORDS
        assert not matched, (
            f"Forbidden automation/control-plane language {matched} found in {filename}"
        )


def _scenario(
    scenario_name: str,
    left_bundle: ManualGateBundle,
    right_bundle: ManualGateBundle,
    expected_bundles_equal: bool,
    expected_changed_fields: list[str],
) -> ManualGateComparisonReplayScenario:
    return ManualGateComparisonReplayScenario(
        scenario_name=scenario_name,
        left_bundle=left_bundle,
        right_bundle=right_bundle,
        expected_bundles_equal=expected_bundles_equal,
        expected_changed_fields=expected_changed_fields,
    )


def _bundle(
    correlation_value: str,
    review_ready: bool = True,
    manual_review_required: bool = False,
    missing_components: list[PacketMissingComponent] | None = None,
) -> ManualGateBundle:
    review_report = ReviewReport(
        packet_id=f"review-packet:{correlation_value}",
        correlation_id=CorrelationId(value=correlation_value),
        review_ready=review_ready,
        report_headline="Candidate 4 manual gate comparison-replay fixture.",
        readiness_summary="Candidate 4 manual gate comparison-replay fixture summary.",
        key_findings=["Candidate 4 manual gate comparison-replay fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=["Confirm bounded review evidence is complete."],
        final_inspection_focus="Minimal bounded review confirmation only.",
        manual_review_required=manual_review_required,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return format_manual_gate_bundle(packet, report)
