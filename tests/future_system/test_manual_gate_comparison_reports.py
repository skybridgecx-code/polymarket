"""Structural and deterministic checks for manual gate comparison report rendering."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.bundles import ManualGateBundle, format_manual_gate_bundle
from future_system.manual_gate.comparison_reports import (
    ManualGateComparisonReport,
    render_manual_gate_comparison_report,
)
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


def test_equal_comparison_renders_deterministically_with_no_changed_fields() -> None:
    comparison = compare_manual_gate_bundles(
        _bundle(correlation_value="corr-1"),
        _bundle(correlation_value="corr-1"),
    )

    report_a = render_manual_gate_comparison_report(comparison)
    report_b = render_manual_gate_comparison_report(comparison)

    assert isinstance(report_a, ManualGateComparisonReport)
    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.bundles_equal is True
    assert report_a.changed_fields == []


def test_disposition_change_comparison_renders_deterministically() -> None:
    left = _bundle(
        correlation_value="corr-2",
        review_ready=True,
        manual_review_required=False,
        missing_components=[],
    )
    right = _bundle(
        correlation_value="corr-2",
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
    )

    comparison = compare_manual_gate_bundles(left, right)
    report_a = render_manual_gate_comparison_report(comparison)
    report_b = render_manual_gate_comparison_report(comparison)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.bundles_equal is False
    assert "disposition" in report_a.changed_fields


def test_review_ready_and_manual_action_required_changes_appear_in_changed_fields() -> None:
    left = _bundle(correlation_value="corr-3")
    right = left.model_copy(
        update={
            "review_ready": False,
            "manual_action_required": False,
        }
    )

    comparison = compare_manual_gate_bundles(left, right)
    report = render_manual_gate_comparison_report(comparison)

    assert "review_ready" in report.changed_fields
    assert "manual_action_required" in report.changed_fields


def test_reason_and_follow_up_deltas_are_preserved_exactly() -> None:
    left = _bundle(correlation_value="corr-4")
    right = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={
                    "reasons": ["b_reason", "a_reason", "c_reason"],
                    "required_follow_up": ["f-2", "f-3", "f-1"],
                }
            )
        }
    )
    left = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={
                    "reasons": ["z_reason", "a_reason", "z_reason"],
                    "required_follow_up": ["f-3", "f-4", "f-4"],
                }
            )
        }
    )

    comparison = compare_manual_gate_bundles(left, right)
    report = render_manual_gate_comparison_report(comparison)

    assert report.changed_fields == ["reasons", "required_follow_up"]
    assert report.added_reasons == ["b_reason", "c_reason"]
    assert report.removed_reasons == ["z_reason"]
    assert report.added_required_follow_up == ["f-1", "f-2"]
    assert report.removed_required_follow_up == ["f-4"]


def test_repeated_render_is_deterministic() -> None:
    comparison = compare_manual_gate_bundles(
        _bundle(correlation_value="corr-5"),
        _bundle(correlation_value="corr-6"),
    )

    report_a = render_manual_gate_comparison_report(comparison)
    report_b = render_manual_gate_comparison_report(comparison)

    assert report_a.model_dump() == report_b.model_dump()


def test_typed_correlation_id_is_preserved() -> None:
    comparison = compare_manual_gate_bundles(
        _bundle(correlation_value="corr-left"),
        _bundle(correlation_value="corr-right"),
    )

    report = render_manual_gate_comparison_report(comparison)

    assert isinstance(report.left_correlation_id, CorrelationId)
    assert isinstance(report.right_correlation_id, CorrelationId)


def test_report_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "comparison_reports.py"):
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
    for filename in ("__init__.py", "comparison_reports.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_CONTROL_WORDS
        assert not matched, (
            f"Forbidden automation/control-plane language {matched} found in {filename}"
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
        report_headline="Candidate 3 manual gate comparison-report fixture.",
        readiness_summary="Candidate 3 manual gate comparison-report fixture summary.",
        key_findings=["Candidate 3 manual gate comparison-report fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=["Confirm bounded review evidence is complete."],
        final_inspection_focus="Minimal bounded review confirmation only.",
        manual_review_required=manual_review_required,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return format_manual_gate_bundle(packet, report)
