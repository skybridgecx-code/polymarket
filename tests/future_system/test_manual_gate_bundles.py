"""Structural and deterministic checks for manual gate bundle formatting."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from future_system.manual_gate.bundles import (
    ManualGateBundle,
    format_manual_gate_bundle,
    format_manual_gate_replay_bundle,
)
from future_system.manual_gate.packets import (
    ManualGateDisposition,
    ManualGatePacket,
    build_manual_gate_packet,
)
from future_system.manual_gate.replay import (
    ManualGateReplayResult,
    ManualGateReplayScenario,
    run_manual_gate_replay,
)
from future_system.manual_gate.reports import ManualGateReport, render_manual_gate_report
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


def test_ready_packet_report_bundle_deterministically() -> None:
    packet, report = _packet_and_report(
        review_ready=True,
        manual_review_required=False,
    )

    bundle_a = format_manual_gate_bundle(packet, report)
    bundle_b = format_manual_gate_bundle(packet, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL
    assert bundle_a.bundle_headline == (
        f"Manual gate packet {packet.packet_id} is bundled for manual approval inspection."
    )


def test_needs_more_evidence_packet_report_bundle_deterministically() -> None:
    packet, report = _packet_and_report(
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        recommended_checks=["Inspect the packet for absent audit records."],
        final_inspection_focus=(
            "Inspect absent packet components before any further review."
        ),
    )

    bundle_a = format_manual_gate_bundle(packet, report)
    bundle_b = format_manual_gate_bundle(packet, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE
    assert bundle_a.bundle_headline == (
        f"Manual gate packet {packet.packet_id} is bundled with explicit manual limits; "
        "missing evidence blocks review."
    )


def test_hold_packet_report_bundle_deterministically() -> None:
    packet, report = _packet_and_report(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    bundle_a = format_manual_gate_bundle(packet, report)
    bundle_b = format_manual_gate_bundle(packet, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.HOLD
    assert bundle_a.bundle_headline == (
        f"Manual gate packet {packet.packet_id} is bundled on hold for manual review."
    )


def test_ready_replay_result_converts_deterministically_to_bundle() -> None:
    replay_result = _replay_result(
        review_ready=True,
        manual_review_required=False,
    )

    bundle_a = format_manual_gate_replay_bundle(replay_result)
    bundle_b = format_manual_gate_replay_bundle(replay_result)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL


def test_needs_more_evidence_replay_result_converts_deterministically_to_bundle() -> None:
    replay_result = _replay_result(
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        recommended_checks=["Inspect the packet for absent audit records."],
        final_inspection_focus=(
            "Inspect absent packet components before any further review."
        ),
    )

    bundle_a = format_manual_gate_replay_bundle(replay_result)
    bundle_b = format_manual_gate_replay_bundle(replay_result)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE


def test_hold_replay_result_converts_deterministically_to_bundle() -> None:
    replay_result = _replay_result(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    bundle_a = format_manual_gate_replay_bundle(replay_result)
    bundle_b = format_manual_gate_replay_bundle(replay_result)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.disposition is ManualGateDisposition.HOLD


def test_repeated_replay_to_bundle_conversion_is_deterministic() -> None:
    replay_result = _replay_result(
        review_ready=True,
        manual_review_required=False,
    )

    bundle_a = format_manual_gate_replay_bundle(replay_result)
    bundle_b = format_manual_gate_replay_bundle(replay_result)

    assert bundle_a.model_dump() == bundle_b.model_dump()


def test_replay_to_bundle_result_mirrors_replay_packet_state() -> None:
    replay_result = _replay_result(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    bundle = format_manual_gate_replay_bundle(replay_result)

    assert bundle.packet_id == replay_result.gate_packet.packet_id
    assert bundle.correlation_id == replay_result.gate_packet.correlation_id
    assert bundle.disposition is replay_result.disposition
    assert bundle.packet.model_dump() == replay_result.gate_packet.model_dump()
    assert bundle.review_ready is replay_result.review_ready
    assert bundle.manual_action_required is replay_result.manual_action_required


def test_replay_to_bundle_helper_matches_manual_composition() -> None:
    replay_result = _replay_result(
        review_ready=False,
        manual_review_required=True,
        missing_components=[PacketMissingComponent.AUDIT_RECORDS],
        recommended_checks=["Inspect the packet for absent audit records."],
        final_inspection_focus=(
            "Inspect absent packet components before any further review."
        ),
    )

    helper_bundle = format_manual_gate_replay_bundle(replay_result)
    manual_bundle = format_manual_gate_bundle(
        replay_result.gate_packet,
        render_manual_gate_report(replay_result.gate_packet),
    )

    assert helper_bundle.model_dump() == manual_bundle.model_dump()


def test_mismatched_packet_ids_raise_bounded_alignment_error() -> None:
    packet, report = _packet_and_report(review_ready=True, manual_review_required=False)
    mismatched_report = report.model_copy(update={"packet_id": "manual-gate:other"})

    with pytest.raises(ValueError, match="manual_gate_bundle_packet_mismatch"):
        format_manual_gate_bundle(packet, mismatched_report)


def test_mismatched_correlation_ids_raise_bounded_alignment_error() -> None:
    packet, report = _packet_and_report(review_ready=True, manual_review_required=False)
    mismatched_report = report.model_copy(
        update={"correlation_id": CorrelationId(value="corr-mismatch")}
    )

    with pytest.raises(ValueError, match="manual_gate_bundle_correlation_mismatch"):
        format_manual_gate_bundle(packet, mismatched_report)


def test_mismatched_disposition_raises_bounded_alignment_error() -> None:
    packet, report = _packet_and_report(review_ready=True, manual_review_required=False)
    mismatched_report = report.model_copy(update={"disposition": ManualGateDisposition.HOLD})

    with pytest.raises(ValueError, match="manual_gate_bundle_disposition_mismatch"):
        format_manual_gate_bundle(packet, mismatched_report)


def test_repeated_formatting_is_deterministic() -> None:
    packet, report = _packet_and_report(review_ready=True, manual_review_required=False)

    bundle_a = format_manual_gate_bundle(packet, report)
    bundle_b = format_manual_gate_bundle(packet, report)

    assert bundle_a.model_dump() == bundle_b.model_dump()


def test_bundle_fields_mirror_packet_report_state() -> None:
    packet, report = _packet_and_report(
        review_ready=False,
        manual_review_required=True,
        recommended_checks=["Inspect attribution trail consistency."],
        final_inspection_focus="Inspect attribution trail consistency.",
    )

    bundle = format_manual_gate_bundle(packet, report)

    assert bundle.packet_id == packet.packet_id
    assert bundle.correlation_id == packet.correlation_id
    assert bundle.disposition is packet.disposition
    assert bundle.packet.model_dump() == packet.model_dump()
    assert bundle.report.model_dump() == report.model_dump()
    assert bundle.review_ready is packet.review_ready
    assert bundle.review_ready is report.review_ready
    assert bundle.manual_action_required is packet.manual_action_required
    assert bundle.manual_action_required is report.manual_action_required


def test_bundle_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "bundles.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, f"Forbidden semantic word(s) {matched} found in {filename}"


def test_bundle_model_has_no_forbidden_fields() -> None:
    for field_name in ManualGateBundle.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ManualGateBundle"
        )


def test_no_widened_automation_control_plane_language_is_introduced() -> None:
    for filename in ("__init__.py", "bundles.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text().lower()
        source_words = set(re.findall(r"[a-z]+", source))
        matched = source_words & _FORBIDDEN_AUTOMATION_CONTROL_WORDS
        assert not matched, (
            f"Forbidden automation/control-plane language {matched} found in {filename}"
        )


def _packet_and_report(
    review_ready: bool,
    manual_review_required: bool,
    missing_components: list[PacketMissingComponent] | None = None,
    recommended_checks: list[str] | None = None,
    final_inspection_focus: str = "Minimal bounded review confirmation only.",
) -> tuple[ManualGatePacket, ManualGateReport]:
    review_report = _review_report(
        review_ready=review_ready,
        manual_review_required=manual_review_required,
        missing_components=missing_components,
        recommended_checks=recommended_checks,
        final_inspection_focus=final_inspection_focus,
    )
    packet = build_manual_gate_packet(review_report)
    report = render_manual_gate_report(packet)
    return packet, report


def _replay_result(
    review_ready: bool,
    manual_review_required: bool,
    missing_components: list[PacketMissingComponent] | None = None,
    recommended_checks: list[str] | None = None,
    final_inspection_focus: str = "Minimal bounded review confirmation only.",
) -> ManualGateReplayResult:
    review_report = _review_report(
        review_ready=review_ready,
        manual_review_required=manual_review_required,
        missing_components=missing_components,
        recommended_checks=recommended_checks,
        final_inspection_focus=final_inspection_focus,
    )
    scenario = ManualGateReplayScenario(
        scenario_name="bundle-replay-fixture",
        input_report=review_report,
        expected_disposition=build_manual_gate_packet(review_report).disposition,
        expected_review_ready=review_ready,
        expected_manual_action_required=True,
    )
    return run_manual_gate_replay(scenario)


def _review_report(
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
        report_headline="Candidate 2 manual gate bundle fixture.",
        readiness_summary="Candidate 2 manual gate bundle fixture summary.",
        key_findings=["Candidate 2 manual gate bundle fixture finding."],
        missing_components=missing_components or [],
        recommended_checks=recommended_checks
        or ["Confirm the packet contents stay unchanged during bounded review."],
        final_inspection_focus=final_inspection_focus,
        manual_review_required=manual_review_required,
    )
