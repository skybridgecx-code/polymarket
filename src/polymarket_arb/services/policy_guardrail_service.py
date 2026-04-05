from __future__ import annotations

from typing import Literal

from polymarket_arb.config import Settings
from polymarket_arb.models.execution import PaperTradeResult
from polymarket_arb.models.policy import PolicyDecision


class PolicyGuardrailService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, *, result: PaperTradeResult) -> PolicyDecision:
        observed_slippage_bps = (
            result.slippage_assumption.total_bps
            if result.slippage_assumption is not None
            else None
        )

        if result.status == "rejected":
            return self._decision(
                decision="deny",
                decision_reason="upstream_result_rejected",
                explanation=(
                    "Denied because the paper-trade planner or simulator already rejected "
                    "the result upstream."
                ),
                active_policy_rules=["deny_upstream_rejected_result"],
                observed_slippage_bps=observed_slippage_bps,
            )

        if self._settings.paper_trade_circuit_breaker_active:
            return self._decision(
                decision="hold",
                decision_reason="circuit_breaker_active",
                explanation=(
                    "Held because the paper-trade circuit breaker is active and policy "
                    "does not allow progression past that state."
                ),
                active_policy_rules=["hold_if_circuit_breaker_active"],
                observed_slippage_bps=observed_slippage_bps,
            )

        if (
            observed_slippage_bps is not None
            and observed_slippage_bps > self._settings.paper_trade_policy_max_slippage_bps
        ):
            return self._decision(
                decision="hold",
                decision_reason="slippage_above_policy_cap",
                explanation=(
                    "Held because the simulated slippage assumption exceeds the configured "
                    "policy cap."
                ),
                active_policy_rules=["hold_if_slippage_above_cap"],
                observed_slippage_bps=observed_slippage_bps,
            )

        return self._decision(
            decision="allow",
            decision_reason="passes_policy",
            explanation=(
                "Allowed because the paper-trade result was accepted upstream and does not "
                "trip the current policy guardrails."
            ),
            active_policy_rules=["allow_if_upstream_accepted_and_within_policy"],
            observed_slippage_bps=observed_slippage_bps,
        )

    def _decision(
        self,
        *,
        decision: Literal["allow", "hold", "deny"],
        decision_reason: str,
        explanation: str,
        active_policy_rules: list[str],
        observed_slippage_bps: int | None,
    ) -> PolicyDecision:
        return PolicyDecision(
            decision=decision,
            decision_reason=decision_reason,
            explanation=explanation,
            active_policy_rules=active_policy_rules,
            manual_override_requested=False,
            manual_override_reason=None,
            manual_override_actor=None,
            manual_override_status="not_requested",
            circuit_breaker_active=self._settings.paper_trade_circuit_breaker_active,
            circuit_breaker_reason=self._settings.paper_trade_circuit_breaker_reason,
            circuit_breaker_scope="paper_trade",
            configured_max_slippage_bps=self._settings.paper_trade_policy_max_slippage_bps,
            observed_slippage_bps=observed_slippage_bps,
        )
