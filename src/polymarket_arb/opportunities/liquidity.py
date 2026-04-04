from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from polymarket_arb.models.normalized import PriceLevel
from polymarket_arb.opportunities.fees import fee_amount_for_buy_shares

_ONE = Decimal("1")
_ZERO = Decimal("0")


@dataclass(frozen=True)
class BundleLegInput:
    market_id: str
    question: str
    outcome: str
    token_id: str
    asks: list[PriceLevel]
    best_ask: Decimal | None
    base_fee_bps: int


@dataclass(frozen=True)
class LegFillSummary:
    market_id: str
    question: str
    outcome: str
    token_id: str
    best_ask: Decimal | None
    quantity: Decimal | None
    average_fill_price: Decimal | None
    fee_bps: int | None


@dataclass(frozen=True)
class BundleEvaluation:
    quantity: Decimal
    gross_edge: Decimal | None
    estimated_fee: Decimal | None
    net_edge: Decimal | None
    rejection_reason: str | None
    explanation: str
    legs: list[LegFillSummary]


@dataclass
class _Cursor:
    leg: BundleLegInput
    level_index: int = 0
    remaining_at_level: Decimal = _ZERO
    filled_quantity: Decimal = _ZERO
    raw_cost: Decimal = _ZERO

    def __post_init__(self) -> None:
        if self.leg.asks:
            self.remaining_at_level = self.leg.asks[0].size

    def current_level(self) -> PriceLevel | None:
        if self.level_index >= len(self.leg.asks):
            return None
        return self.leg.asks[self.level_index]

    def unit_total_cost(self) -> Decimal | None:
        level = self.current_level()
        if level is None:
            return None
        fee = fee_amount_for_buy_shares(
            shares=_ONE,
            price=level.price,
            base_fee_bps=self.leg.base_fee_bps,
        )
        return level.price + fee

    def take(self, quantity: Decimal) -> Decimal:
        level = self.current_level()
        if level is None:
            raise ValueError("Cannot take liquidity from an exhausted cursor.")

        self.filled_quantity += quantity
        self.raw_cost += quantity * level.price
        fee_cost = fee_amount_for_buy_shares(
            shares=quantity,
            price=level.price,
            base_fee_bps=self.leg.base_fee_bps,
        )
        self.remaining_at_level -= quantity
        if self.remaining_at_level == _ZERO:
            self.level_index += 1
            if self.level_index < len(self.leg.asks):
                self.remaining_at_level = self.leg.asks[self.level_index].size
        return fee_cost

    def summary(self) -> LegFillSummary:
        average_fill_price = None
        quantity = None
        if self.filled_quantity > _ZERO:
            quantity = self.filled_quantity
            average_fill_price = self.raw_cost / self.filled_quantity

        return LegFillSummary(
            market_id=self.leg.market_id,
            question=self.leg.question,
            outcome=self.leg.outcome,
            token_id=self.leg.token_id,
            best_ask=self.leg.best_ask,
            quantity=quantity,
            average_fill_price=average_fill_price,
            fee_bps=self.leg.base_fee_bps,
        )


def evaluate_bundle(legs: list[BundleLegInput]) -> BundleEvaluation:
    if not legs:
        return BundleEvaluation(
            quantity=_ZERO,
            gross_edge=None,
            estimated_fee=None,
            net_edge=None,
            rejection_reason="missing_legs",
            explanation="Rejected because the candidate did not contain any executable legs.",
            legs=[],
        )

    missing_liquidity = [leg.token_id for leg in legs if not leg.asks]
    if missing_liquidity:
        summaries = [
            LegFillSummary(
                market_id=leg.market_id,
                question=leg.question,
                outcome=leg.outcome,
                token_id=leg.token_id,
                best_ask=leg.best_ask,
                quantity=None,
                average_fill_price=None,
                fee_bps=leg.base_fee_bps,
            )
            for leg in legs
        ]
        return BundleEvaluation(
            quantity=_ZERO,
            gross_edge=None,
            estimated_fee=None,
            net_edge=None,
            rejection_reason="insufficient_liquidity",
            explanation=(
                "Rejected because displayed asks were missing for token(s) "
                + ", ".join(sorted(missing_liquidity))
                + "."
            ),
            legs=summaries,
        )

    cursors = [_Cursor(leg=leg) for leg in legs]
    total_fee = _ZERO
    stop_reason = "insufficient_liquidity"
    stop_unit_cost: Decimal | None = None

    while True:
        current_unit_cost = _ZERO
        step_size: Decimal | None = None

        for cursor in cursors:
            unit_cost = cursor.unit_total_cost()
            if unit_cost is None:
                stop_reason = "insufficient_liquidity"
                step_size = None
                break

            current_unit_cost += unit_cost
            step_size = cursor.remaining_at_level if step_size is None else min(
                step_size,
                cursor.remaining_at_level,
            )

        if step_size is None:
            stop_unit_cost = current_unit_cost if current_unit_cost > _ZERO else None
            break

        if current_unit_cost >= _ONE:
            stop_reason = "no_positive_net_edge"
            stop_unit_cost = current_unit_cost
            break

        for cursor in cursors:
            total_fee += cursor.take(step_size)

    quantity = sum((cursor.filled_quantity for cursor in cursors[:1]), start=_ZERO)
    summaries = [cursor.summary() for cursor in cursors]

    if quantity == _ZERO:
        top_level_raw_cost = sum(leg.asks[0].price for leg in legs)
        top_level_fee_cost = sum(
            fee_amount_for_buy_shares(
                shares=_ONE,
                price=leg.asks[0].price,
                base_fee_bps=leg.base_fee_bps,
            )
            for leg in legs
        )
        if top_level_raw_cost >= _ONE:
            rejection_reason = "no_gross_edge"
        elif top_level_raw_cost + top_level_fee_cost >= _ONE:
            rejection_reason = "fees_exceed_edge"
        else:
            rejection_reason = stop_reason

        explanation = (
            "Rejected because the first executable bundle costs "
            f"{top_level_raw_cost + top_level_fee_cost:.5f} USDC including fees, "
            "which does not leave a positive net edge."
        )
        if rejection_reason == "insufficient_liquidity":
            explanation = (
                "Rejected because displayed ask liquidity was exhausted before one full bundle."
            )

        return BundleEvaluation(
            quantity=_ZERO,
            gross_edge=_ZERO,
            estimated_fee=_ZERO,
            net_edge=_ZERO,
            rejection_reason=rejection_reason,
            explanation=explanation,
            legs=summaries,
        )

    raw_cost = sum(cursor.raw_cost for cursor in cursors)
    gross_edge = quantity - raw_cost
    net_edge = gross_edge - total_fee

    if stop_reason == "insufficient_liquidity":
        explanation = (
            f"Accepted over {quantity:.6f} shares until displayed ask liquidity ran out; "
            f"gross edge is {gross_edge:.5f} USDC before {total_fee:.5f} USDC of taker fees."
        )
    else:
        next_bundle_cost = stop_unit_cost if stop_unit_cost is not None else _ONE
        explanation = (
            f"Accepted over {quantity:.6f} shares; the next marginal bundle costs "
            f"{next_bundle_cost:.5f} USDC including fees, so additional size is rejected."
        )

    return BundleEvaluation(
        quantity=quantity,
        gross_edge=gross_edge,
        estimated_fee=total_fee,
        net_edge=net_edge,
        rejection_reason=None,
        explanation=explanation,
        legs=summaries,
    )
