from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

from polymarket_arb.models.policy import PolicyDecision


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"

    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


class ProposedExecutionLeg(BaseModel):
    market_id: str
    question: str
    outcome: str
    token_id: str
    reference_price: Decimal | None
    proposed_quantity: Decimal | None
    fee_bps: int | None

    def to_output(self) -> dict[str, Any]:
        return {
            "market_id": self.market_id,
            "question": self.question,
            "outcome": self.outcome,
            "token_id": self.token_id,
            "reference_price": _decimal_to_string(self.reference_price),
            "proposed_quantity": _decimal_to_string(self.proposed_quantity),
            "fee_bps": self.fee_bps,
        }


class SlippageAssumption(BaseModel):
    model: Literal["flat_plus_leg_plus_utilization_bps"]
    base_bps: int
    additional_leg_bps: int
    utilization_bps: int
    total_bps: int
    capacity_utilization: Decimal
    explanation: str

    def to_output(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "base_bps": self.base_bps,
            "additional_leg_bps": self.additional_leg_bps,
            "utilization_bps": self.utilization_bps,
            "total_bps": self.total_bps,
            "capacity_utilization": _decimal_to_string(self.capacity_utilization),
            "explanation": self.explanation,
        }


class SimulatedExecutionLeg(BaseModel):
    token_id: str
    reference_price: Decimal
    simulated_fill_price: Decimal
    quantity: Decimal
    gross_cost: Decimal
    fees: Decimal

    def to_output(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "reference_price": _decimal_to_string(self.reference_price),
            "simulated_fill_price": _decimal_to_string(self.simulated_fill_price),
            "quantity": _decimal_to_string(self.quantity),
            "gross_cost": _decimal_to_string(self.gross_cost),
            "fees": _decimal_to_string(self.fees),
        }


class SimulatedExecutionResult(BaseModel):
    simulated_entry_cost: Decimal
    simulated_fees: Decimal
    simulated_total_cost: Decimal
    simulated_payout_assumption: Decimal
    simulated_gross_edge_cents: Decimal
    simulated_net_edge_cents: Decimal
    simulated_legs: list[SimulatedExecutionLeg]

    def to_output(self) -> dict[str, Any]:
        return {
            "simulated_entry_cost": _decimal_to_string(self.simulated_entry_cost),
            "simulated_fees": _decimal_to_string(self.simulated_fees),
            "simulated_total_cost": _decimal_to_string(self.simulated_total_cost),
            "simulated_payout_assumption": _decimal_to_string(self.simulated_payout_assumption),
            "simulated_gross_edge_cents": _decimal_to_string(self.simulated_gross_edge_cents),
            "simulated_net_edge_cents": _decimal_to_string(self.simulated_net_edge_cents),
            "simulated_legs": [leg.to_output() for leg in self.simulated_legs],
        }


class ExecutionPlan(BaseModel):
    plan_id: str
    source_opportunity_reference: str
    opportunity_type: Literal["binary_complement", "neg_risk_basket"]
    source_opportunity_status: Literal["accepted", "rejected"]
    source_opportunity_explanation: str
    displayed_capacity: Decimal | None
    proposed_legs: list[ProposedExecutionLeg]
    proposed_size: Decimal | None
    estimated_entry_cost: Decimal | None
    estimated_fees: Decimal | None
    slippage_assumption: SlippageAssumption | None
    status: Literal["accepted", "rejected"]
    rejection_reason: str | None
    explanation: str
    risk_flags: list[str]


class PaperTradeResult(BaseModel):
    plan_id: str
    source_opportunity_reference: str
    opportunity_type: Literal["binary_complement", "neg_risk_basket"]
    source_opportunity_status: Literal["accepted", "rejected"]
    source_opportunity_explanation: str
    displayed_capacity: Decimal | None
    proposed_legs: list[ProposedExecutionLeg]
    proposed_size: Decimal | None
    estimated_entry_cost: Decimal | None
    estimated_fees: Decimal | None
    slippage_assumption: SlippageAssumption | None
    status: Literal["accepted", "rejected"]
    rejection_reason: str | None
    explanation: str
    risk_flags: list[str]
    simulated_result: SimulatedExecutionResult | None
    policy_decision: PolicyDecision | None = None

    def to_output(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "source_opportunity_reference": self.source_opportunity_reference,
            "opportunity_type": self.opportunity_type,
            "source_opportunity_status": self.source_opportunity_status,
            "source_opportunity_explanation": self.source_opportunity_explanation,
            "displayed_capacity": _decimal_to_string(self.displayed_capacity),
            "proposed_legs": [leg.to_output() for leg in self.proposed_legs],
            "proposed_size": _decimal_to_string(self.proposed_size),
            "estimated_entry_cost": _decimal_to_string(self.estimated_entry_cost),
            "estimated_fees": _decimal_to_string(self.estimated_fees),
            "slippage_assumption": (
                self.slippage_assumption.to_output()
                if self.slippage_assumption is not None
                else None
            ),
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "explanation": self.explanation,
            "risk_flags": self.risk_flags,
            "simulated_result": (
                self.simulated_result.to_output()
                if self.simulated_result is not None
                else None
            ),
            "policy_decision": (
                self.policy_decision.to_output()
                if self.policy_decision is not None
                else None
            ),
        }
