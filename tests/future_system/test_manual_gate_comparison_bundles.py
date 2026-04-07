"""Structural and deterministic checks for manual gate comparison bundles."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from future_system.manual_gate.bundles import ManualGateBundle, format_manual_gate_bundle
from future_system.manual_gate.comparison_bundles import (
    ManualGateComparisonBundle,
    format_manual_gate_comparison_bundle,
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


def test_equal_comparison_report_bundles_deterministically() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-1"),
        right=_bundle(correlation_value="corr-1"),
    )

    bundle_a = format_manual_gate_comparison_bundle(comparison, report)
    bundle_b = format_manual_gate_comparison_bundle(comparison, report)

    assert isinstance(bundle_a, ManualGateComparisonBundle)
    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.bundles_equal is True
    assert bundle_a.bundle_headline == (
        "Manual gate comparison bundle is aligned with no bounded differences."
    )


def test_unequal_comparison_report_bundles_deterministically() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-2"),
        right=_bundle(
            correlation_value="corr-2",
            review_ready=False,
            manual_review_required=True,
            missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        ),
    )

    bundle_a = format_manual_gate_comparison_bundle(comparison, report)
    bundle_b = format_manual_gate_comparison_bundle(comparison, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.bundles_equal is False
    assert bundle_a.bundle_headline == (
        "Manual gate comparison bundle is aligned with bounded differences."
    )


def test_left_packet_id_mismatch_raises_bounded_alignment_error() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-3"),
        right=_bundle(correlation_value="corr-3"),
    )
    mismatched_report = report.model_copy(update={"left_packet_id": "manual-gate:other-left"})

    with pytest.raises(
        ValueError,
        match="manual_gate_comparison_bundle_left_packet_mismatch",
    ):
        format_manual_gate_comparison_bundle(comparison, mismatched_report)


def test_right_packet_id_mismatch_raises_bounded_alignment_error() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-4"),
        right=_bundle(correlation_value="corr-4"),
    )
    mismatched_report = report.model_copy(
        update={"right_packet_id": "manual-gate:other-right"}
    )

    with pytest.raises(
        ValueError,
        match="manual_gate_comparison_bundle_right_packet_mismatch",
    ):
        format_manual_gate_comparison_bundle(comparison, mismatched_report)


def test_left_correlation_id_mismatch_raises_bounded_alignment_error() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-5"),
        right=_bundle(correlation_value="corr-5"),
    )
    mismatched_report = report.model_copy(
        update={"left_correlation_id": CorrelationId(value="corr-left-mismatch")}
    )

    with pytest.raises(
        ValueError,
        match="manual_gate_comparison_bundle_left_correlation_mismatch",
    ):
        format_manual_gate_comparison_bundle(comparison, mismatched_report)


def test_right_correlation_id_mismatch_raises_bounded_alignment_error() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-6"),
        right=_bundle(correlation_value="corr-6"),
    )
    mismatched_report = report.model_copy(
        update={"right_correlation_id": CorrelationId(value="corr-right-mismatch")}
    )

    with pytest.raises(
        ValueError,
        match="manual_gate_comparison_bundle_right_correlation_mismatch",
    ):
        format_manual_gate_comparison_bundle(comparison, mismatched_report)


def test_bundles_equal_mismatch_raises_bounded_alignment_error() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-7"),
        right=_bundle(correlation_value="corr-7"),
    )
    mismatched_report = report.model_copy(update={"bundles_equal": False})

    with pytest.raises(
        ValueError,
        match="manual_gate_comparison_bundle_bundles_equal_mismatch",
    ):
        format_manual_gate_comparison_bundle(comparison, mismatched_report)


def test_repeated_formatting_is_deterministic() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-8"),
        right=_bundle(correlation_value="corr-8"),
    )

    bundle_a = format_manual_gate_comparison_bundle(comparison, report)
    bundle_b = format_manual_gate_comparison_bundle(comparison, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()


def test_typed_correlation_id_is_preserved() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-left"),
        right=_bundle(correlation_value="corr-right"),
    )

    bundle = format_manual_gate_comparison_bundle(comparison, report)

    assert isinstance(bundle.left_correlation_id, CorrelationId)
    assert isinstance(bundle.right_correlation_id, CorrelationId)


def test_bundle_fields_mirror_comparison_report_state() -> None:
    comparison, report = _comparison_and_report(
        left=_bundle(correlation_value="corr-9"),
        right=_bundle(
            correlation_value="corr-9",
            review_ready=False,
            manual_review_required=True,
            missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        ),
    )

    bundle = format_manual_gate_comparison_bundle(comparison, report)

    assert bundle.left_packet_id == comparison.left_packet_id
    assert bundle.right_packet_id == comparison.right_packet_id
    assert bundle.left_correlation_id == comparison.left_correlation_id
    assert bundle.right_correlation_id == comparison.right_correlation_id
    assert bundle.comparison.model_dump() == comparison.model_dump()
    assert bundle.report.model_dump() == report.model_dump()
    assert bundle.bundles_equal is comparison.bundles_equal
    assert bundle.bundles_equal is report.bundles_equal


def test_comparison_bundle_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "comparison_bundles.py"):
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
    for filename in ("__init__.py", "comparison_bundles.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_CONTROL_WORDS
        assert not matched, (
            f"Forbidden automation/control-plane language {matched} found in {filename}"
        )


def _comparison_and_report(
    left: ManualGateBundle,
    right: ManualGateBundle,
):
    comparison = compare_manual_gate_bundles(left, right)
    report = render_manual_gate_comparison_report(comparison)
    return comparison, report


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
        report_headline="Candidate 3 manual gate comparison-bundle fixture.",
        readiness_summary="Candidate 3 manual gate comparison-bundle fixture summary.",
        key_findings=["Candidate 3 manual gate comparison-bundle fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=["Confirm bounded review evidence is complete."],
        final_inspection_focus="Minimal bounded review confirmation only.",
        manual_review_required=manual_review_required,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return format_manual_gate_bundle(packet, report)

