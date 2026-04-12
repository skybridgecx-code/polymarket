"""Deterministic parsing and validation for model-like reasoning outputs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from future_system.reasoning_contracts.models import ReasoningOutputPacket, ReasoningParseError


def parse_reasoning_output(payload: Mapping[str, Any] | str) -> ReasoningOutputPacket:
    """Parse and validate reasoning output from mapping or JSON string."""

    if isinstance(payload, str):
        payload_mapping = _parse_json_payload(payload)
    elif isinstance(payload, Mapping):
        payload_mapping = dict(payload)
    else:
        raise ReasoningParseError("Reasoning output must be a mapping or JSON string.")

    try:
        return ReasoningOutputPacket.model_validate(payload_mapping)
    except (ValidationError, ValueError, TypeError) as exc:
        raise ReasoningParseError("Reasoning output failed schema validation.") from exc


def _parse_json_payload(payload: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ReasoningParseError("Malformed reasoning output JSON.") from exc

    if not isinstance(parsed, dict):
        raise ReasoningParseError("Reasoning output JSON must decode to an object.")

    return parsed
