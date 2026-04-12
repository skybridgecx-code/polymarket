"""Model validation tests for future_system.reasoning_contracts contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.reasoning_contracts.models import ReasoningInputPacket, ReasoningOutputPacket
from pydantic import ValidationError

_INPUT_FIXTURE_PATH = Path("tests/fixtures/future_system/reasoning/reasoning_inputs.json")
_OUTPUT_FIXTURE_PATH = Path("tests/fixtures/future_system/reasoning/reasoning_outputs.json")


def test_reasoning_contract_models_accept_valid_payloads() -> None:
    input_packet = ReasoningInputPacket.model_validate(_input_case("strong_complete"))
    output_packet = ReasoningOutputPacket.model_validate(_output_case("valid"))

    assert input_packet.theme_id == "theme_ctx_strong"
    assert input_packet.prompt_version == "v1"
    assert output_packet.recommended_posture == "candidate"


def test_invalid_recommended_posture_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReasoningOutputPacket.model_validate(_output_case("invalid_posture"))


def test_required_non_empty_fields_are_enforced() -> None:
    invalid = _output_case("valid")
    invalid["thesis"] = "   "

    with pytest.raises(ValidationError):
        ReasoningOutputPacket.model_validate(invalid)

    missing = _output_case("invalid_missing_fields")
    with pytest.raises(ValidationError):
        ReasoningOutputPacket.model_validate(missing)


def test_list_normalization_is_deterministic() -> None:
    payload = _output_case("valid")
    payload["key_drivers"] = ["  Driver A  ", "", "Driver B", "   "]
    payload["missing_information"] = ["  Missing X ", "", "Missing Y"]
    payload["uncertainty_notes"] = ["  Uncertain A  ", " "]
    payload["analyst_flags"] = ["  flag_one  ", "", "flag_two"]

    packet = ReasoningOutputPacket.model_validate(payload)

    assert packet.key_drivers == ["Driver A", "Driver B"]
    assert packet.missing_information == ["Missing X", "Missing Y"]
    assert packet.uncertainty_notes == ["Uncertain A"]
    assert packet.analyst_flags == ["flag_one", "flag_two"]


def _input_case(case_name: str) -> dict[str, object]:
    payload = json.loads(_INPUT_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item["input_packet"])
    raise AssertionError(f"Missing reasoning input fixture case: {case_name}")


def _output_case(case_name: str) -> dict[str, object]:
    payload = json.loads(_OUTPUT_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item["output"])
    raise AssertionError(f"Missing reasoning output fixture case: {case_name}")
