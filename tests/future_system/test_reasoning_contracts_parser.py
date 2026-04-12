"""Parser behavior tests for deterministic reasoning contract output validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.reasoning_contracts.models import ReasoningParseError
from future_system.reasoning_contracts.parser import parse_reasoning_output

_FIXTURE_PATH = Path("tests/fixtures/future_system/reasoning/reasoning_outputs.json")


def test_valid_mapping_parses_into_reasoning_output_packet() -> None:
    payload = _output_case("valid")

    packet = parse_reasoning_output(payload)

    assert packet.theme_id == "theme_ctx_strong"
    assert packet.recommended_posture == "candidate"


def test_valid_json_string_parses_into_reasoning_output_packet() -> None:
    payload = _output_case("valid")

    packet = parse_reasoning_output(json.dumps(payload))

    assert packet.thesis.startswith("Cross-market")


def test_malformed_json_raises_reasoning_parse_error() -> None:
    malformed = "{\"theme_id\":\"theme_ctx_strong\","

    with pytest.raises(ReasoningParseError):
        parse_reasoning_output(malformed)


def test_invalid_posture_raises_reasoning_parse_error() -> None:
    payload = _output_case("invalid_posture")

    with pytest.raises(ReasoningParseError):
        parse_reasoning_output(payload)


def test_missing_required_fields_raise_reasoning_parse_error() -> None:
    payload = _output_case("invalid_missing_fields")

    with pytest.raises(ReasoningParseError):
        parse_reasoning_output(payload)


def test_string_list_normalization_is_deterministic() -> None:
    payload = _output_case("valid")
    payload["key_drivers"] = ["  Driver A ", "", "Driver B", "  "]
    payload["missing_information"] = ["  Missing 1  ", ""]
    payload["uncertainty_notes"] = ["  Uncertain 1", "   "]
    payload["analyst_flags"] = ["  flag_1  ", "", "flag_2"]

    packet = parse_reasoning_output(payload)

    assert packet.key_drivers == ["Driver A", "Driver B"]
    assert packet.missing_information == ["Missing 1"]
    assert packet.uncertainty_notes == ["Uncertain 1"]
    assert packet.analyst_flags == ["flag_1", "flag_2"]


def _output_case(case_name: str) -> dict[str, object]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item["output"])
    raise AssertionError(f"Missing reasoning output fixture case: {case_name}")
