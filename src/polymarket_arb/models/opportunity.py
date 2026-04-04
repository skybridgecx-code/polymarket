from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"

    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


class OpportunityLeg(BaseModel):
    market_id: str
    question: str
    outcome: str
    token_id: str
    best_ask: Decimal | None
    average_fill_price: Decimal | None
    quantity: Decimal | None
    fee_bps: int | None

    def to_output(self) -> dict[str, Any]:
        return {
            "market_id": self.market_id,
            "question": self.question,
            "outcome": self.outcome,
            "token_id": self.token_id,
            "best_ask": _decimal_to_string(self.best_ask),
            "average_fill_price": _decimal_to_string(self.average_fill_price),
            "quantity": _decimal_to_string(self.quantity),
            "fee_bps": self.fee_bps,
        }


class OpportunityCandidate(BaseModel):
    event_slug: str
    opportunity_type: Literal["binary_complement", "neg_risk_basket"]
    legs: list[OpportunityLeg]
    gross_edge_cents: Decimal | None
    estimated_fee_cents: Decimal | None
    net_edge_cents: Decimal | None
    capacity_shares_or_notional: Decimal | None
    status: Literal["accepted", "rejected"]
    rejection_reason: str | None
    explanation: str

    def to_output(self) -> dict[str, Any]:
        return {
            "event_slug": self.event_slug,
            "opportunity_type": self.opportunity_type,
            "legs": [leg.to_output() for leg in self.legs],
            "gross_edge_cents": _decimal_to_string(self.gross_edge_cents),
            "estimated_fee_cents": _decimal_to_string(self.estimated_fee_cents),
            "net_edge_cents": _decimal_to_string(self.net_edge_cents),
            "capacity_shares_or_notional": _decimal_to_string(self.capacity_shares_or_notional),
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "explanation": self.explanation,
        }
