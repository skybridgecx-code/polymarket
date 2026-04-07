"""Structural and deterministic checks for manual gate replay scenarios."""

from __future__ import annotations

import re
from pathlib import Path

from future_system.manual_gate.packets import (
    ManualGateDisposition,
    build_manual_gate_packet,
)
from future_system.manual_gate.replay import (
    ManualGateReplayResult,
    ManualGateReplayScenario,
    run_manual_gate_replay,
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


def test_ready_report_replays_to_ready_for_manual_approval() -> None:
    scenario = _ready_scenario()

    replay = run_manual_gate_replay(scenario)

    assert replay.disposition is ManualGateDisposition.READY_FOR_MANUAL_APPROVAL
    assert replay.review_ready is scenario.expected_review_ready
    assert replay.manual_action_required is scenario.expected_manual_action_required


def test_missing_component_report_replays_to_needs_more_evidence() -> None:
    scenario = _missing_component_scenario()

    replay = run_manual_gate_replay(scenario)

    assert replay.disposition is ManualGateDisposition.NEEDS_MORE_EVIDENCE
    assert replay.review_ready is scenario.expected_review_ready
    assert replay.manual_action_required is scenario.expected_manual_action_required


def test_manual_review_not_ready_report_replays_to_hold() -> None:
    scenario = _hold_scenario()

    replay = run_manual_gate_replay(scenario)

    assert replay.disposition is ManualGateDisposition.HOLD
    assert replay.review_ready is scenario.expected_review_ready
    assert replay.manual_action_required is scenario.expected_manual_action_required


def test_repeated_replay_of_same_scenario_is_deterministic() -> None:
    scenario = _ready_scenario()

    replay_a = run_manual_gate_replay(scenario)
    replay_b = run_manual_gate_replay(scenario)

    assert replay_a.model_dump() == replay_b.model_dump()


def test_result_fields_exactly_mirror_produced_gate_packet() -> None:
    scenario = _missing_component_scenario()

    replay = run_manual_gate_replay(scenario)
    expected_packet = build_manual_gate_packet(scenario.input_report)

    assert replay.gate_packet.model_dump() == expected_packet.model_dump()
    assert replay.disposition is replay.gate_packet.disposition
    assert replay.review_ready is replay.gate_packet.review_ready
    assert replay.manual_action_required is replay.gate_packet.manual_action_required
    assert replay.disposition is scenario.expected_disposition


def test_replay_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "replay.py"):
        source = (_MANUAL_GATE_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_replay_models_have_no_forbidden_fields() -> None:
    for model in (ManualGateReplayScenario, ManualGateReplayResult):
        for field_name in model.model_fields:
            parts = set(field_name.lower().split("_"))
            matched = parts & _FORBIDDEN_FIELD_TERMS
            assert not matched, (
                f"Forbidden term(s) {matched} found in field "
                f"{field_name!r} of {model.__name__}"
            )


def test_rejected_for_scope_is_not_forced_via_fake_unsupported_input() -> None:
    scenarios = [_ready_scenario(), _missing_component_scenario(), _hold_scenario()]

    replays = [run_manual_gate_replay(scenario) for scenario in scenarios]

    assert all(
        replay.disposition is not ManualGateDisposition.REJECTED_FOR_SCOPE
        for replay in replays
    )


def _ready_scenario() -> ManualGateReplayScenario:
    return ManualGateReplayScenario(
        scenario_name="ready",
        input_report=_report(
            review_ready=True,
            manual_review_required=False,
            missing_components=[],
            recommended_checks=["Confirm bounded review evidence is complete."],
            final_inspection_focus="Minimal bounded review confirmation only.",
        ),
        expected_disposition=ManualGateDisposition.READY_FOR_MANUAL_APPROVAL,
        expected_review_ready=True,
        expected_manual_action_required=True,
    )


def _missing_component_scenario() -> ManualGateReplayScenario:
    return ManualGateReplayScenario(
        scenario_name="missing-component",
        input_report=_report(
            review_ready=False,
            manual_review_required=True,
            missing_components=[PacketMissingComponent.ORDERED_TRACE],
            recommended_checks=["Inspect the packet for absent ordered trace records."],
            final_inspection_focus=(
                "Inspect absent packet components before any further review."
            ),
        ),
        expected_disposition=ManualGateDisposition.NEEDS_MORE_EVIDENCE,
        expected_review_ready=False,
        expected_manual_action_required=True,
    )


def _hold_scenario() -> ManualGateReplayScenario:
    return ManualGateReplayScenario(
        scenario_name="manual-review-not-ready",
        input_report=_report(
            review_ready=False,
            manual_review_required=True,
            missing_components=[],
            recommended_checks=["Inspect attribution trail consistency."],
            final_inspection_focus="Inspect attribution trail consistency.",
        ),
        expected_disposition=ManualGateDisposition.HOLD,
        expected_review_ready=False,
        expected_manual_action_required=True,
    )


def _report(
    review_ready: bool,
    manual_review_required: bool,
    missing_components: list[PacketMissingComponent],
    recommended_checks: list[str],
    final_inspection_focus: str,
) -> ReviewReport:
    return ReviewReport(
        packet_id="review-packet:corr-1",
        correlation_id=CorrelationId(value="corr-1"),
        review_ready=review_ready,
        report_headline="Candidate 2 manual gate replay fixture.",
        readiness_summary="Candidate 2 manual gate replay fixture summary.",
        key_findings=["Candidate 2 manual gate replay fixture finding."],
        missing_components=missing_components,
        recommended_checks=recommended_checks,
        final_inspection_focus=final_inspection_focus,
        manual_review_required=manual_review_required,
    )
