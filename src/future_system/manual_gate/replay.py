"""Deterministic in-memory replay harness for manual gate scenarios."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.packets import (
    ManualGateDisposition,
    ManualGatePacket,
    build_manual_gate_packet,
)
from future_system.review.reports import ReviewReport


class ManualGateReplayScenario(BaseModel):
    """Fixed in-memory scenario for manual gate replay."""

    scenario_name: str
    input_report: ReviewReport
    expected_disposition: ManualGateDisposition
    expected_review_ready: bool
    expected_manual_action_required: bool


class ManualGateReplayResult(BaseModel):
    """Deterministic result for one replayed manual gate scenario."""

    scenario_name: str
    gate_packet: ManualGatePacket
    disposition: ManualGateDisposition
    review_ready: bool
    manual_action_required: bool


def run_manual_gate_replay(
    scenario: ManualGateReplayScenario,
) -> ManualGateReplayResult:
    """Replay one manual gate scenario using a typed review report."""

    gate_packet = build_manual_gate_packet(scenario.input_report)

    return ManualGateReplayResult(
        scenario_name=scenario.scenario_name,
        gate_packet=gate_packet,
        disposition=gate_packet.disposition,
        review_ready=gate_packet.review_ready,
        manual_action_required=gate_packet.manual_action_required,
    )
