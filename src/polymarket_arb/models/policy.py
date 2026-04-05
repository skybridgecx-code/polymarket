from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: Literal["allow", "hold", "deny"]
    decision_reason: str
    explanation: str
    active_policy_rules: list[str]
    manual_override_requested: bool
    manual_override_reason: str | None
    manual_override_actor: str | None
    manual_override_status: Literal["not_requested", "requested", "approved", "rejected"]
    circuit_breaker_active: bool
    circuit_breaker_reason: str | None
    circuit_breaker_scope: str
    configured_max_slippage_bps: int
    observed_slippage_bps: int | None

    def to_output(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
