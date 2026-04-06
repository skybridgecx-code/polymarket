"""Structural and deterministic checks for manual gate packets."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.packets import (
    ManualGateDisposition,
    ManualGatePacket,
    build_manual_gate_packet,
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


def test_review_ready_report_produces_ready_for_manual_approval() -> None:
    report = _report(review_ready=True, manual_review_required=False)

    packet_a = build_manual_gate_packet(report)
    packet_b = build_manual_gate_packet(report)

    assert packet_a.model_dump() == packet_b.model_dump()
    assert packet_a.packet_id == "manual-gate:review-packet:corr-1"
    assert packet_a.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL
    assert packet_a.review_ready is True
    assert packet_a.manual_action_required is True
    assert packet_a.reasons == ["review_ready"]
    assert packet_a.required_follow_up == [
        "Perform manual inspection before any approval decision.",
        "Minimal bounded review confirmation only.",
    ]


def test_incomplete_report_produces_needs_more_evidence() -> None:
    report = _report(
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        recommended_checks=["Inspect the packet for absent audit records."],
        final_inspection_focus="Inspect absent packet components before any further review.",
    )

    packet = build_manual_gate_packet(report)

    assert packet.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE
    assert packet.review_ready is False
    assert packet.manual_action_required is True
    assert packet.reasons == [
        "missing_components_present",
        "missing_component:audit_records",
    ]
    assert packet.required_follow_up == [
        "Inspect missing component: audit_records.",
        "Inspect the packet for absent audit records.",
    ]


def test_not_ready_report_without_missing_components_produces_hold() -> None:
    report = _report(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    packet = build_manual_gate_packet(report)

    assert packet.disposition is ManualGateDisposition.HOLD
    assert packet.reasons == ["manual_review_required", "review_not_ready"]
    assert packet.required_follow_up == [
        "Inspect attribution trail consistency.",
        "Inspect attribution trail consistency.",
    ]


def test_rejected_for_scope_is_available_but_not_used_for_typed_reports() -> None:
    report = _report(review_ready=True, manual_review_required=False)

    packet = build_manual_gate_packet(report)

    assert ManualGateDisposition.REJECTED_FOR_SCOPE.value == "rejected_for_scope"
    assert packet.disposition is not ManualGateDisposition.REJECTED_FOR_SCOPE


def test_manual_gate_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "packets.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_manual_gate_model_has_no_forbidden_fields() -> None:
    for field_name in ManualGatePacket.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ManualGatePacket"
        )


def _report(
    review_ready: bool,
    manual_review_required: bool,
    missing_components: list[PacketMissingComponent] | None = None,
    recommended_checks: list[str] | None = None,
    final_inspection_focus: str = "Minimal bounded review confirmation only.",
) -> ReviewReport:
    return ReviewReport(
        packet_id="review-packet:corr-1",
        correlation_id=CorrelationId(value="corr-1"),
        review_ready=review_ready,
        report_headline="Candidate 2 manual gate fixture.",
        readiness_summary="Candidate 2 manual gate fixture summary.",
        key_findings=["Candidate 2 manual gate fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=recommended_checks or [
            "Confirm the packet contents stay unchanged during bounded review."
        ],
        final_inspection_focus=final_inspection_focus,
        manual_review_required=manual_review_required,
    )
