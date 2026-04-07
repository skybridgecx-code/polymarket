"""Structural and deterministic checks for manual gate bundle comparisons."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.bundles import ManualGateBundle, format_manual_gate_bundle
from future_system.manual_gate.comparisons import (
    ManualGateComparison,
    compare_manual_gate_bundles,
)
from future_system.manual_gate.packets import ManualGateDisposition, build_manual_gate_packet
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


def test_equal_bundles_compare_as_equal_with_no_deltas() -> None:
    left = _bundle(correlation_value="corr-1")
    right = _bundle(correlation_value="corr-1")

    comparison = compare_manual_gate_bundles(left, right)

    assert isinstance(comparison, ManualGateComparison)
    assert comparison.bundles_equal is True
    assert comparison.same_packet_id is True
    assert comparison.same_correlation_id is True
    assert isinstance(comparison.left_correlation_id, CorrelationId)
    assert isinstance(comparison.right_correlation_id, CorrelationId)
    assert comparison.left_correlation_id == left.correlation_id
    assert comparison.right_correlation_id == right.correlation_id
    assert comparison.disposition_changed is False
    assert comparison.review_ready_changed is False
    assert comparison.manual_action_required_changed is False
    assert comparison.added_reasons == []
    assert comparison.removed_reasons == []
    assert comparison.added_required_follow_up == []
    assert comparison.removed_required_follow_up == []


def test_differing_disposition_is_detected_deterministically() -> None:
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

    comparison_a = compare_manual_gate_bundles(left, right)
    comparison_b = compare_manual_gate_bundles(left, right)

    assert comparison_a.model_dump() == comparison_b.model_dump()
    assert comparison_a.disposition_changed is True
    assert comparison_a.left_disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL
    assert comparison_a.right_disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE
    assert comparison_a.bundles_equal is False


def test_differing_review_ready_is_detected_deterministically() -> None:
    left = _bundle(
        correlation_value="corr-3",
        review_ready=False,
        manual_review_required=True,
    )
    right = _bundle(
        correlation_value="corr-3",
        review_ready=True,
        manual_review_required=True,
    )

    comparison = compare_manual_gate_bundles(left, right)

    assert comparison.left_disposition is ManualGateDisposition.HOLD
    assert comparison.right_disposition is ManualGateDisposition.HOLD
    assert comparison.disposition_changed is False
    assert comparison.review_ready_changed is True
    assert comparison.bundles_equal is False


def test_differing_manual_action_required_is_detected_deterministically() -> None:
    left = _bundle(correlation_value="corr-4")
    right = left.model_copy(update={"manual_action_required": False})

    comparison = compare_manual_gate_bundles(left, right)

    assert comparison.manual_action_required_changed is True
    assert comparison.bundles_equal is False


def test_added_removed_reasons_are_explicit_and_stable() -> None:
    left = _bundle(correlation_value="corr-5")
    right = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={"reasons": ["b_reason", "a_reason", "c_reason"]}
            )
        }
    )
    left = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={"reasons": ["z_reason", "a_reason", "z_reason"]}
            )
        }
    )

    comparison = compare_manual_gate_bundles(left, right)

    assert comparison.added_reasons == ["b_reason", "c_reason"]
    assert comparison.removed_reasons == ["z_reason"]


def test_added_removed_required_follow_up_are_explicit_and_stable() -> None:
    left = _bundle(correlation_value="corr-6")
    right = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={"required_follow_up": ["f-2", "f-3", "f-1"]}
            )
        }
    )
    left = left.model_copy(
        update={
            "packet": left.packet.model_copy(
                update={"required_follow_up": ["f-3", "f-4", "f-4"]}
            )
        }
    )

    comparison = compare_manual_gate_bundles(left, right)

    assert comparison.added_required_follow_up == ["f-1", "f-2"]
    assert comparison.removed_required_follow_up == ["f-4"]


def test_differing_packet_ids_and_correlation_ids_are_surfaced_as_booleans() -> None:
    left = _bundle(correlation_value="corr-left")
    right = _bundle(correlation_value="corr-right")

    comparison = compare_manual_gate_bundles(left, right)

    assert comparison.same_packet_id is False
    assert comparison.same_correlation_id is False
    assert isinstance(comparison.left_correlation_id, CorrelationId)
    assert isinstance(comparison.right_correlation_id, CorrelationId)
    assert comparison.left_correlation_id == left.correlation_id
    assert comparison.right_correlation_id == right.correlation_id
    assert comparison.bundles_equal is False


def test_repeated_comparison_is_deterministic() -> None:
    left = _bundle(correlation_value="corr-7")
    right = _bundle(
        correlation_value="corr-7",
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
    )

    comparison_a = compare_manual_gate_bundles(left, right)
    comparison_b = compare_manual_gate_bundles(left, right)

    assert comparison_a.model_dump() == comparison_b.model_dump()


def test_comparison_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "comparisons.py"):
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
    for filename in ("__init__.py", "comparisons.py"):
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
        report_headline="Candidate 3 manual gate comparison fixture.",
        readiness_summary="Candidate 3 manual gate comparison fixture summary.",
        key_findings=["Candidate 3 manual gate comparison fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=["Confirm bounded review evidence is complete."],
        final_inspection_focus="Minimal bounded review confirmation only.",
        manual_review_required=manual_review_required,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return format_manual_gate_bundle(packet, report)
