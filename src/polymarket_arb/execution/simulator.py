from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from polymarket_arb.config import Settings
from polymarket_arb.models.execution import (
    ExecutionPlan,
    PaperTradeResult,
    SimulatedExecutionLeg,
    SimulatedExecutionResult,
    SlippageAssumption,
)
from polymarket_arb.opportunities.fees import fee_amount_for_buy_shares

_BPS_DENOMINATOR = Decimal("10000")
_CENTS = Decimal("100")
_ONE = Decimal("1")
_PRICE_PRECISION = Decimal("0.00001")
_ZERO = Decimal("0")


class PaperTradeSimulator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def simulate(self, *, plan: ExecutionPlan) -> PaperTradeResult:
        if plan.status == "rejected":
            return PaperTradeResult(
                **plan.model_dump(),
                simulated_result=None,
            )

        assert plan.proposed_size is not None
        slippage_assumption = self._slippage_assumption(plan=plan)

        simulated_legs: list[SimulatedExecutionLeg] = []
        simulated_entry_cost = _ZERO
        simulated_fees = _ZERO
        slippage_multiplier = _ONE + (Decimal(slippage_assumption.total_bps) / _BPS_DENOMINATOR)

        for leg in plan.proposed_legs:
            assert leg.reference_price is not None
            assert leg.proposed_quantity is not None
            assert leg.fee_bps is not None

            simulated_fill_price = min(
                _ONE,
                (leg.reference_price * slippage_multiplier).quantize(
                    _PRICE_PRECISION,
                    rounding=ROUND_HALF_UP,
                ),
            )
            gross_cost = simulated_fill_price * leg.proposed_quantity
            fees = fee_amount_for_buy_shares(
                shares=leg.proposed_quantity,
                price=simulated_fill_price,
                base_fee_bps=leg.fee_bps,
            )
            simulated_entry_cost += gross_cost
            simulated_fees += fees
            simulated_legs.append(
                SimulatedExecutionLeg(
                    token_id=leg.token_id,
                    reference_price=leg.reference_price,
                    simulated_fill_price=simulated_fill_price,
                    quantity=leg.proposed_quantity,
                    gross_cost=gross_cost,
                    fees=fees,
                )
            )

        simulated_total_cost = simulated_entry_cost + simulated_fees
        simulated_payout_assumption = plan.proposed_size
        simulated_gross_edge_cents = (simulated_payout_assumption - simulated_entry_cost) * _CENTS
        simulated_net_edge_cents = (simulated_payout_assumption - simulated_total_cost) * _CENTS
        simulated_result = SimulatedExecutionResult(
            simulated_entry_cost=simulated_entry_cost,
            simulated_fees=simulated_fees,
            simulated_total_cost=simulated_total_cost,
            simulated_payout_assumption=simulated_payout_assumption,
            simulated_gross_edge_cents=simulated_gross_edge_cents,
            simulated_net_edge_cents=simulated_net_edge_cents,
            simulated_legs=simulated_legs,
        )

        risk_flags = set(plan.risk_flags)
        if simulated_net_edge_cents <= self._settings.paper_trade_min_simulated_edge_cents:
            risk_flags.add("thin_simulated_edge")
            rejected_plan = plan.model_copy(
                update={
                    "slippage_assumption": slippage_assumption,
                    "status": "rejected",
                    "rejection_reason": "kill_switch_simulated_edge_below_buffer",
                    "explanation": (
                        "Rejected because simulated edge after slippage and fees "
                        f"falls below the configured safety buffer of "
                        f"{self._settings.paper_trade_min_simulated_edge_cents} cents."
                    ),
                    "risk_flags": sorted(risk_flags),
                }
            )
            return PaperTradeResult(
                **rejected_plan.model_dump(),
                simulated_result=simulated_result,
            )

        accepted_plan = plan.model_copy(
            update={
                "slippage_assumption": slippage_assumption,
                "status": "accepted",
                "rejection_reason": None,
                "explanation": (
                    "Accepted for paper trading because simulated edge remains above the "
                    "configured slippage and safety-buffer thresholds."
                ),
                "risk_flags": sorted(risk_flags),
            }
        )
        return PaperTradeResult(
            **accepted_plan.model_dump(),
            simulated_result=simulated_result,
        )

    def _slippage_assumption(self, *, plan: ExecutionPlan) -> SlippageAssumption:
        assert plan.proposed_size is not None
        assert plan.proposed_legs
        displayed_capacity = plan.displayed_capacity
        capacity_utilization = (
            _ZERO
            if displayed_capacity is None or displayed_capacity == _ZERO
            else plan.proposed_size / displayed_capacity
        )
        additional_leg_bps = self._settings.paper_trade_additional_leg_slippage_bps * max(
            len(plan.proposed_legs) - 1,
            0,
        )
        utilization_bps = int(
            (
                capacity_utilization * self._settings.paper_trade_utilization_slippage_bps
            ).to_integral_value(rounding=ROUND_HALF_UP)
        )
        total_bps = (
            self._settings.paper_trade_base_slippage_bps
            + additional_leg_bps
            + utilization_bps
        )
        return SlippageAssumption(
            model="flat_plus_leg_plus_utilization_bps",
            base_bps=self._settings.paper_trade_base_slippage_bps,
            additional_leg_bps=additional_leg_bps,
            utilization_bps=utilization_bps,
            total_bps=total_bps,
            capacity_utilization=capacity_utilization,
            explanation=(
                "Applies a fixed per-plan slippage buffer made of a base amount, "
                "a multi-leg penalty, and a displayed-capacity utilization penalty."
            ),
        )
