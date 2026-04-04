from __future__ import annotations

from decimal import Decimal

from polymarket_arb.config import Settings
from polymarket_arb.models.execution import ExecutionPlan, ProposedExecutionLeg
from polymarket_arb.models.opportunity import OpportunityCandidate
from polymarket_arb.opportunities.fees import fee_amount_for_buy_shares

_ZERO = Decimal("0")


class ExecutionPlanBuilder:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_plan(self, *, opportunity: OpportunityCandidate) -> ExecutionPlan:
        source_reference = self._source_reference(opportunity)
        if opportunity.status != "accepted":
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="source_opportunity_rejected",
                explanation=(
                    "Rejected because the originating opportunity was already rejected "
                    "by the opportunity engine."
                ),
                risk_flags=["source_candidate_rejected"],
            )

        if not opportunity.legs:
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="missing_legs",
                explanation=(
                    "Rejected because the originating opportunity exposed "
                    "no executable legs."
                ),
                risk_flags=["missing_legs"],
            )

        if (
            opportunity.capacity_shares_or_notional is None
            or opportunity.capacity_shares_or_notional <= 0
        ):
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="missing_capacity_signal",
                explanation=(
                    "Rejected because the originating opportunity does not expose "
                    "positive executable capacity."
                ),
                risk_flags=["missing_capacity_signal"],
            )

        if any(
            leg.average_fill_price is None or leg.quantity is None or leg.fee_bps is None
            for leg in opportunity.legs
        ):
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="missing_plan_inputs",
                explanation=(
                    "Rejected because one or more legs are missing average fill price, "
                    "quantity, or fee data needed for paper-trade planning."
                ),
                risk_flags=["missing_plan_inputs"],
            )

        available_capacity = min(
            [opportunity.capacity_shares_or_notional]
            + [leg.quantity for leg in opportunity.legs if leg.quantity is not None]
        )
        proposed_size = min(available_capacity, self._settings.paper_trade_max_size)

        if proposed_size < self._settings.paper_trade_min_size:
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="proposed_size_below_minimum",
                explanation=(
                    "Rejected because displayed capacity is below the paper-trade minimum size "
                    f"of {self._settings.paper_trade_min_size} shares."
                ),
                risk_flags=["capacity_below_policy_floor"],
                proposed_size=proposed_size,
            )

        capacity_utilization = proposed_size / available_capacity
        if capacity_utilization > self._settings.paper_trade_max_capacity_utilization:
            return self._rejected_plan(
                opportunity=opportunity,
                source_reference=source_reference,
                rejection_reason="kill_switch_high_capacity_utilization",
                explanation=(
                    "Rejected because the plan would consume too much displayed capacity "
                    f"({capacity_utilization:.3f} of available size)."
                ),
                risk_flags=["high_capacity_utilization"],
                proposed_size=proposed_size,
            )

        estimated_entry_cost = _ZERO
        estimated_fees = _ZERO
        proposed_legs: list[ProposedExecutionLeg] = []
        for leg in opportunity.legs:
            assert leg.average_fill_price is not None
            assert leg.fee_bps is not None
            estimated_entry_cost += leg.average_fill_price * proposed_size
            estimated_fees += fee_amount_for_buy_shares(
                shares=proposed_size,
                price=leg.average_fill_price,
                base_fee_bps=leg.fee_bps,
            )
            proposed_legs.append(
                ProposedExecutionLeg(
                    market_id=leg.market_id,
                    question=leg.question,
                    outcome=leg.outcome,
                    token_id=leg.token_id,
                    reference_price=leg.average_fill_price,
                    proposed_quantity=proposed_size,
                    fee_bps=leg.fee_bps,
                )
            )

        plan_id = self._plan_id(source_reference=source_reference, proposed_size=proposed_size)
        risk_flags = {"source_candidate_accepted"}
        if len(proposed_legs) > 1:
            risk_flags.add("multi_leg_bundle")
        if proposed_size < available_capacity:
            risk_flags.add("size_clipped_to_plan_limit")

        return ExecutionPlan(
            plan_id=plan_id,
            source_opportunity_reference=source_reference,
            opportunity_type=opportunity.opportunity_type,
            source_opportunity_status=opportunity.status,
            source_opportunity_explanation=opportunity.explanation,
            displayed_capacity=available_capacity,
            proposed_legs=proposed_legs,
            proposed_size=proposed_size,
            estimated_entry_cost=estimated_entry_cost,
            estimated_fees=estimated_fees,
            slippage_assumption=None,
            status="accepted",
            rejection_reason=None,
            explanation=(
                f"Planned {proposed_size} shares from opportunity {source_reference} "
                "using the opportunity engine's displayed fill estimates."
            ),
            risk_flags=sorted(risk_flags),
        )

    def _rejected_plan(
        self,
        *,
        opportunity: OpportunityCandidate,
        source_reference: str,
        rejection_reason: str,
        explanation: str,
        risk_flags: list[str],
        proposed_size: Decimal | None = None,
    ) -> ExecutionPlan:
        plan_id = self._plan_id(source_reference=source_reference, proposed_size=proposed_size)
        return ExecutionPlan(
            plan_id=plan_id,
            source_opportunity_reference=source_reference,
            opportunity_type=opportunity.opportunity_type,
            source_opportunity_status=opportunity.status,
            source_opportunity_explanation=opportunity.explanation,
            displayed_capacity=opportunity.capacity_shares_or_notional,
            proposed_legs=[
                ProposedExecutionLeg(
                    market_id=leg.market_id,
                    question=leg.question,
                    outcome=leg.outcome,
                    token_id=leg.token_id,
                    reference_price=leg.average_fill_price,
                    proposed_quantity=proposed_size,
                    fee_bps=leg.fee_bps,
                )
                for leg in opportunity.legs
            ],
            proposed_size=proposed_size,
            estimated_entry_cost=None,
            estimated_fees=None,
            slippage_assumption=None,
            status="rejected",
            rejection_reason=rejection_reason,
            explanation=explanation,
            risk_flags=sorted(set(risk_flags)),
        )

    def _source_reference(self, opportunity: OpportunityCandidate) -> str:
        token_ids = "+".join(leg.token_id for leg in opportunity.legs) or "no-legs"
        return f"{opportunity.event_slug}:{opportunity.opportunity_type}:{token_ids}"

    def _plan_id(self, *, source_reference: str, proposed_size: Decimal | None) -> str:
        size_text = "na" if proposed_size is None else format(proposed_size.normalize(), "f")
        return f"paper:{source_reference}:size={size_text}"
