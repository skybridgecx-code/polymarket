"""Pluggable offline analyst protocol for dry-run runtime orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket

AnalystResponsePayload = Mapping[str, Any] | str


@runtime_checkable
class AnalystProtocol(Protocol):
    """Offline analyst boundary returning model-like reasoning output payloads."""

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        """Return a mapping or JSON-string payload parseable by reasoning parser."""
