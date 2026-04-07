"""Structural and deterministic checks for manual gate report rendering."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.packets import (
    ManualGateDisposition,
    ManualGatePacket,
    build_manual_gate_packet,
)
from future_system.manual_gate.reports import (
    ManualGateReport,
    render_manual_gate_report,
)
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
_FORBIDDEN_FIELD_TERMS = frozenset(
    {
        "venue",
        "auth",
        "credential",
        "sign",
        "position",
        "submit",
        "private",
        "order",
        "live",
    }
)
_FORBIDDEN_AUTOMATION_WORDS = frozenset(
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
    }
)


def test_ready_packet_renders_ready_for_manual_approval_deterministically() -> None:
    packet = _packet(review_ready=True, manual_review_required=False)

    report_a = render_manual_gate_report(packet)
    report_b = render_manual_gate_report(packet)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL
    assert report_a.report_headline == (
        f"Manual gate packet {packet.packet_id} is ready for manual approval review."
    )


def test_needs_more_evidence_packet_renders_missing_evidence_deterministically() -> None:
    packet = _packet(
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        recommended_checks=["Inspect the packet for absent audit records."],
        final_inspection_focus="Inspect absent packet components before any further review.",
    )

    report_a = render_manual_gate_report(packet)
    report_b = render_manual_gate_report(packet)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE
    assert report_a.report_headline == (
        f"Manual gate packet {packet.packet_id} needs more evidence "
        "before manual approval review."
    )
    assert report_a.decision_summary == (
        "Manual gate review must pause until missing evidence "
        "is supplied for inspection."
    )


def test_hold_packet_renders_hold_manual_review_deterministically() -> None:
    packet = _packet(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    report_a = render_manual_gate_report(packet)
    report_b = render_manual_gate_report(packet)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.disposition is ManualGateDisposition.HOLD
    assert report_a.report_headline == (
        f"Manual gate packet {packet.packet_id} is on hold for manual review."
    )
    assert report_a.decision_summary == (
        "Manual gate review remains on hold because the "
        "source review is not ready."
    )


def test_repeated_render_of_same_packet_is_deterministic() -> None:
    packet = _packet(review_ready=True, manual_review_required=False)

    report_a = render_manual_gate_report(packet)
    report_b = render_manual_gate_report(packet)

    assert report_a.model_dump() == report_b.model_dump()


def test_rendered_fields_mirror_packet_flags() -> None:
    packet = _packet(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    report = render_manual_gate_report(packet)

    assert report.packet_id == packet.packet_id
    assert report.correlation_id == packet.correlation_id
    assert report.disposition is packet.disposition
    assert report.key_reasons == packet.reasons
    assert report.required_follow_up == packet.required_follow_up
    assert report.review_ready is packet.review_ready
    assert report.manual_action_required is packet.manual_action_required


def test_report_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "reports.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_report_model_has_no_forbidden_fields() -> None:
    for field_name in ManualGateReport.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ManualGateReport"
        )


def test_no_widened_automation_language_is_introduced() -> None:
    for filename in ("__init__.py", "reports.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_WORDS
        assert not matched, (
            f"Forbidden automation language {matched} found in {filename}"
        )


def _packet(
    review_ready: bool,
    manual_review_required: bool,
    missing_components: list[PacketMissingComponent] | None = None,
    recommended_checks: list[str] | None = None,
    final_inspection_focus: str = "Minimal bounded review confirmation only.",
) -> ManualGatePacket:
    report = ReviewReport(
        packet_id="review-packet:corr-1",
        correlation_id=CorrelationId(value="corr-1"),
        review_ready=review_ready,
        report_headline="Candidate 2 manual gate report fixture.",
        readiness_summary="Candidate 2 manual gate report fixture summary.",
        key_findings=["Candidate 2 manual gate report fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=recommended_checks or [
            "Confirm the packet contents stay unchanged during bounded review."
        ],
        final_inspection_focus=final_inspection_focus,
        manual_review_required=manual_review_required,
    )
    return build_manual_gate_packet(report)
