from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from polymarket_arb.config import Settings
from polymarket_arb.models.execution import PaperTradeResult, SlippageAssumption
from polymarket_arb.models.policy import PolicyDecision
from polymarket_arb.services.policy_guardrail_service import PolicyGuardrailService


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(
        DATA_DIR=tmp_path / "data",
        STATE_DIR=tmp_path / "state",
        POLY_GAMMA_BASE_URL="https://gamma-api.polymarket.com",
        POLY_CLOB_BASE_URL="https://clob.polymarket.com",
        POLY_DATA_BASE_URL="https://data-api.polymarket.com",
        POLY_WS_MARKET_URL="wss://ws-subscriptions-clob.polymarket.com/ws/market",
    )
    settings.ensure_directories()
    return settings


def _paper_trade_result(
    *,
    status: str,
    rejection_reason: str | None,
    total_bps: int | None,
) -> PaperTradeResult:
    slippage_assumption = None
    if total_bps is not None:
        slippage_assumption = SlippageAssumption(
            model="flat_plus_leg_plus_utilization_bps",
            base_bps=10,
            additional_leg_bps=5,
            utilization_bps=total_bps - 15,
            total_bps=total_bps,
            capacity_utilization=Decimal("0.5"),
            explanation="Test slippage assumption.",
        )

    return PaperTradeResult(
        plan_id="paper:test-plan",
        source_opportunity_reference="event:test",
        opportunity_type="binary_complement",
        source_opportunity_status="accepted" if status == "accepted" else "rejected",
        source_opportunity_explanation="source explanation",
        displayed_capacity=Decimal("10"),
        proposed_legs=[],
        proposed_size=Decimal("10"),
        estimated_entry_cost=Decimal("9"),
        estimated_fees=Decimal("0.1"),
        slippage_assumption=slippage_assumption,
        status=status,  # type: ignore[arg-type]
        rejection_reason=rejection_reason,
        explanation="paper trade explanation",
        risk_flags=[],
        simulated_result=None,
        policy_decision=None,
    )


def test_policy_guardrail_service_allows_upstream_accepted_result_within_cap(
    tmp_path: Path,
) -> None:
    service = PolicyGuardrailService(_settings(tmp_path))
    decision = service.evaluate(
        result=_paper_trade_result(
            status="accepted",
            rejection_reason=None,
            total_bps=22,
        )
    )

    assert isinstance(decision, PolicyDecision)
    assert decision.decision == "allow"
    assert decision.decision_reason == "passes_policy"
    assert decision.observed_slippage_bps == 22
    assert decision.circuit_breaker_active is False
    assert decision.manual_override_status == "not_requested"


def test_policy_guardrail_service_holds_when_slippage_exceeds_configured_cap(
    tmp_path: Path,
) -> None:
    service = PolicyGuardrailService(_settings(tmp_path))
    decision = service.evaluate(
        result=_paper_trade_result(
            status="accepted",
            rejection_reason=None,
            total_bps=25,
        )
    )

    assert decision.decision == "hold"
    assert decision.decision_reason == "slippage_above_policy_cap"
    assert decision.configured_max_slippage_bps == 24
    assert decision.observed_slippage_bps == 25


def test_policy_guardrail_service_denies_upstream_rejected_result(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    settings.paper_trade_circuit_breaker_active = True
    settings.paper_trade_circuit_breaker_reason = "manual_stop_for_test"
    service = PolicyGuardrailService(settings)
    decision = service.evaluate(
        result=_paper_trade_result(
            status="rejected",
            rejection_reason="source_opportunity_rejected",
            total_bps=None,
        )
    )

    assert decision.decision == "deny"
    assert decision.decision_reason == "upstream_result_rejected"
    assert decision.circuit_breaker_active is True
    assert decision.circuit_breaker_reason == "manual_stop_for_test"
