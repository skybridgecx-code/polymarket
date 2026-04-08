"""Structural and deterministic checks for replay-report rendering."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.bundles import ManualGateBundle, format_manual_gate_bundle
from future_system.manual_gate.comparison_replay import (
    ManualGateComparisonReplayResult,
    ManualGateComparisonReplayScenario,
    run_manual_gate_comparison_replay,
)
from future_system.manual_gate.comparison_replay_reports import (
    ManualGateComparisonReplayReport,
    render_manual_gate_comparison_replay_report,
)
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


def test_equal_replay_result_renders_deterministically() -> None:
    replay_result = _replay_result(
        scenario_name="equal",
        left_bundle=_bundle(correlation_value="corr-1"),
        right_bundle=_bundle(correlation_value="corr-1"),
    )

    report_a = render_manual_gate_comparison_replay_report(replay_result)
    report_b = render_manual_gate_comparison_replay_report(replay_result)

    assert isinstance(report_a, ManualGateComparisonReplayReport)
    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.bundles_equal is True
    assert report_a.changed_fields == []


def test_differing_replay_result_renders_deterministically() -> None:
    left = _bundle(correlation_value="corr-2")
    right = left.model_copy(
        update={
            "review_ready": False,
            "manual_action_required": False,
        }
    )
    replay_result = _replay_result(
        scenario_name="different",
        left_bundle=left,
        right_bundle=right,
    )

    report_a = render_manual_gate_comparison_replay_report(replay_result)
    report_b = render_manual_gate_comparison_replay_report(replay_result)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.bundles_equal is False
    assert report_a.changed_fields == ["review_ready", "manual_action_required"]


def test_changed_fields_and_bundles_equal_are_preserved_exactly() -> None:
    left = _bundle(correlation_value="corr-3")
    right = _bundle(
        correlation_value="corr-3",
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
    )
    replay_result = _replay_result(
        scenario_name="preserve",
        left_bundle=left,
        right_bundle=right,
    )

    report = render_manual_gate_comparison_replay_report(replay_result)

    assert report.changed_fields == replay_result.changed_fields
    assert report.bundles_equal is replay_result.bundles_equal


def test_typed_correlation_id_is_preserved() -> None:
    replay_result = _replay_result(
        scenario_name="typed-correlation",
        left_bundle=_bundle(correlation_value="corr-left"),
        right_bundle=_bundle(correlation_value="corr-right"),
    )

    report = render_manual_gate_comparison_replay_report(replay_result)

    assert isinstance(report.left_correlation_id, CorrelationId)
    assert isinstance(report.right_correlation_id, CorrelationId)


def test_repeated_render_is_deterministic() -> None:
    replay_result = _replay_result(
        scenario_name="repeat",
        left_bundle=_bundle(correlation_value="corr-4"),
        right_bundle=_bundle(correlation_value="corr-5"),
    )

    report_a = render_manual_gate_comparison_replay_report(replay_result)
    report_b = render_manual_gate_comparison_replay_report(replay_result)

    assert report_a.model_dump() == report_b.model_dump()


def test_replay_report_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "comparison_replay_reports.py"):
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
    for filename in ("__init__.py", "comparison_replay_reports.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_CONTROL_WORDS
        assert not matched, (
            f"Forbidden automation/control-plane language {matched} found in {filename}"
        )


def _replay_result(
    scenario_name: str,
    left_bundle: ManualGateBundle,
    right_bundle: ManualGateBundle,
) -> ManualGateComparisonReplayResult:
    scenario = ManualGateComparisonReplayScenario(
        scenario_name=scenario_name,
        left_bundle=left_bundle,
        right_bundle=right_bundle,
        expected_bundles_equal=False,
        expected_changed_fields=[],
    )
    return run_manual_gate_comparison_replay(scenario)


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
        report_headline="Candidate 5 manual gate replay-report fixture.",
        readiness_summary="Candidate 5 manual gate replay-report fixture summary.",
        key_findings=["Candidate 5 manual gate replay-report fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=["Confirm bounded review evidence is complete."],
        final_inspection_focus="Minimal bounded review confirmation only.",
        manual_review_required=manual_review_required,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return format_manual_gate_bundle(packet, report)
