from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from polymarket_arb.models.normalized import (
    NormalizedBook,
    NormalizedEvent,
    NormalizedFeeRate,
    NormalizedMarket,
)
from polymarket_arb.models.opportunity import OpportunityCandidate, OpportunityLeg
from polymarket_arb.opportunities.liquidity import (
    BundleEvaluation,
    BundleLegInput,
    LegFillSummary,
    evaluate_bundle,
)

_CENTS = Decimal("100")
_ZERO = Decimal("0")


@dataclass(frozen=True)
class _LegSpec:
    market_id: str
    question: str
    outcome: str
    token_id: str


OpportunityType = Literal["binary_complement", "neg_risk_basket"]


class OpportunityEngine:
    def build_candidates(
        self,
        *,
        events: list[NormalizedEvent],
        books_by_token: dict[str, NormalizedBook],
        fee_rates_by_token: dict[str, NormalizedFeeRate],
    ) -> list[OpportunityCandidate]:
        candidates: list[OpportunityCandidate] = []

        for event in events:
            candidates.append(
                self._build_neg_risk_candidate(
                    event=event,
                    books_by_token=books_by_token,
                    fee_rates_by_token=fee_rates_by_token,
                )
            )
            for market in event.markets:
                candidates.append(
                    self._build_complement_candidate(
                        event=event,
                        market=market,
                        books_by_token=books_by_token,
                        fee_rates_by_token=fee_rates_by_token,
                    )
                )

        candidates.sort(key=self._sort_key)
        return candidates

    def _build_complement_candidate(
        self,
        *,
        event: NormalizedEvent,
        market: NormalizedMarket,
        books_by_token: dict[str, NormalizedBook],
        fee_rates_by_token: dict[str, NormalizedFeeRate],
    ) -> OpportunityCandidate:
        if len(market.outcomes) != 2 or len(market.token_ids) != 2:
            return self._rejected_candidate(
                event_slug=event.slug,
                opportunity_type="binary_complement",
                legs=self._placeholder_legs_from_market(market),
                rejection_reason="not_binary_market",
                explanation=(
                    f"Rejected because market {market.market_id} is not "
                    "a strict two-outcome market."
                ),
            )

        if not market.accepting_orders:
            return self._rejected_candidate(
                event_slug=event.slug,
                opportunity_type="binary_complement",
                legs=self._placeholder_legs_from_market(market),
                rejection_reason="market_not_accepting_orders",
                explanation=f"Rejected because market {market.market_id} is not accepting orders.",
            )

        leg_specs = [
            _LegSpec(
                market_id=market.market_id,
                question=market.question,
                outcome=market.outcomes[index],
                token_id=market.token_ids[index],
            )
            for index in range(2)
        ]
        evaluation = self._evaluate_specs(
            leg_specs=leg_specs,
            books_by_token=books_by_token,
            fee_rates_by_token=fee_rates_by_token,
        )
        return self._candidate_from_evaluation(
            event_slug=event.slug,
            opportunity_type="binary_complement",
            evaluation=evaluation,
        )

    def _build_neg_risk_candidate(
        self,
        *,
        event: NormalizedEvent,
        books_by_token: dict[str, NormalizedBook],
        fee_rates_by_token: dict[str, NormalizedFeeRate],
    ) -> OpportunityCandidate:
        neg_risk_markets = [market for market in event.markets if market.neg_risk]
        if len(neg_risk_markets) < 2:
            return self._rejected_candidate(
                event_slug=event.slug,
                opportunity_type="neg_risk_basket",
                legs=[],
                rejection_reason="not_enough_neg_risk_markets",
                explanation=(
                    "Rejected because the event does not expose at least "
                    "two neg-risk markets."
                ),
            )

        if any(not market.accepting_orders for market in neg_risk_markets):
            return self._rejected_candidate(
                event_slug=event.slug,
                opportunity_type="neg_risk_basket",
                legs=self._placeholder_legs_from_markets(neg_risk_markets),
                rejection_reason="market_not_accepting_orders",
                explanation=(
                    "Rejected because at least one neg-risk market "
                    "is not accepting orders."
                ),
            )

        leg_specs: list[_LegSpec] = []
        for market in neg_risk_markets:
            if len(market.outcomes) != 2 or len(market.token_ids) != 2:
                return self._rejected_candidate(
                    event_slug=event.slug,
                    opportunity_type="neg_risk_basket",
                    legs=self._placeholder_legs_from_markets(neg_risk_markets),
                    rejection_reason="not_binary_market",
                    explanation=(
                        f"Rejected because neg-risk market {market.market_id} "
                        "is not a two-outcome yes/no market."
                    ),
                )

            yes_index = self._yes_index(market.outcomes)
            if yes_index is None:
                return self._rejected_candidate(
                    event_slug=event.slug,
                    opportunity_type="neg_risk_basket",
                    legs=self._placeholder_legs_from_markets(neg_risk_markets),
                    rejection_reason="missing_yes_outcome",
                    explanation=(
                        f"Rejected because neg-risk market {market.market_id} "
                        "does not expose a canonical Yes leg."
                    ),
                )

            leg_specs.append(
                _LegSpec(
                    market_id=market.market_id,
                    question=market.question,
                    outcome=market.outcomes[yes_index],
                    token_id=market.token_ids[yes_index],
                )
            )

        evaluation = self._evaluate_specs(
            leg_specs=leg_specs,
            books_by_token=books_by_token,
            fee_rates_by_token=fee_rates_by_token,
        )
        candidate = self._candidate_from_evaluation(
            event_slug=event.slug,
            opportunity_type="neg_risk_basket",
            evaluation=evaluation,
        )
        if candidate.status == "accepted":
            candidate.explanation = (
                f"{candidate.explanation} Basket uses {len(leg_specs)} "
                f"neg-risk Yes legs from event {event.slug}."
            )
        return candidate

    def _evaluate_specs(
        self,
        *,
        leg_specs: list[_LegSpec],
        books_by_token: dict[str, NormalizedBook],
        fee_rates_by_token: dict[str, NormalizedFeeRate],
    ) -> BundleEvaluation:
        missing_fee_rate = sorted(
            spec.token_id for spec in leg_specs if spec.token_id not in fee_rates_by_token
        )
        if missing_fee_rate:
            return BundleEvaluation(
                quantity=_ZERO,
                gross_edge=None,
                estimated_fee=None,
                net_edge=None,
                rejection_reason="missing_fee_rate",
                explanation=(
                    "Rejected because fee-rate data was unavailable for token(s) "
                    + ", ".join(missing_fee_rate)
                    + "."
                ),
                legs=[
                    self._placeholder_summary(
                        spec=spec,
                        books_by_token=books_by_token,
                        fee_rates_by_token=fee_rates_by_token,
                    )
                    for spec in leg_specs
                ],
            )

        bundle_legs: list[BundleLegInput] = []
        for spec in leg_specs:
            book = books_by_token.get(spec.token_id)
            if book is None:
                return BundleEvaluation(
                    quantity=_ZERO,
                    gross_edge=None,
                    estimated_fee=None,
                    net_edge=None,
                    rejection_reason="missing_orderbook",
                    explanation=(
                        f"Rejected because token {spec.token_id} "
                        "has no orderbook snapshot."
                    ),
                    legs=[
                        self._placeholder_summary(
                            spec=item,
                            books_by_token=books_by_token,
                            fee_rates_by_token=fee_rates_by_token,
                        )
                        for item in leg_specs
                    ],
                )

            fee_rate = fee_rates_by_token[spec.token_id]
            bundle_legs.append(
                BundleLegInput(
                    market_id=spec.market_id,
                    question=spec.question,
                    outcome=spec.outcome,
                    token_id=spec.token_id,
                    asks=book.asks,
                    best_ask=book.best_ask,
                    base_fee_bps=fee_rate.base_fee_bps,
                )
            )

        return evaluate_bundle(bundle_legs)

    def _candidate_from_evaluation(
        self,
        *,
        event_slug: str,
        opportunity_type: OpportunityType,
        evaluation: BundleEvaluation,
    ) -> OpportunityCandidate:
        return OpportunityCandidate(
            event_slug=event_slug,
            opportunity_type=opportunity_type,
            legs=[
                OpportunityLeg(
                    market_id=leg.market_id,
                    question=leg.question,
                    outcome=leg.outcome,
                    token_id=leg.token_id,
                    best_ask=leg.best_ask,
                    average_fill_price=leg.average_fill_price,
                    quantity=leg.quantity,
                    fee_bps=leg.fee_bps,
                )
                for leg in evaluation.legs
            ],
            gross_edge_cents=self._to_cents(evaluation.gross_edge),
            estimated_fee_cents=self._to_cents(evaluation.estimated_fee),
            net_edge_cents=self._to_cents(evaluation.net_edge),
            capacity_shares_or_notional=evaluation.quantity,
            status="accepted" if evaluation.rejection_reason is None else "rejected",
            rejection_reason=evaluation.rejection_reason,
            explanation=evaluation.explanation,
        )

    def _rejected_candidate(
        self,
        *,
        event_slug: str,
        opportunity_type: OpportunityType,
        legs: list[OpportunityLeg],
        rejection_reason: str,
        explanation: str,
    ) -> OpportunityCandidate:
        return OpportunityCandidate(
            event_slug=event_slug,
            opportunity_type=opportunity_type,
            legs=legs,
            gross_edge_cents=None,
            estimated_fee_cents=None,
            net_edge_cents=None,
            capacity_shares_or_notional=_ZERO,
            status="rejected",
            rejection_reason=rejection_reason,
            explanation=explanation,
        )

    def _placeholder_legs_from_market(self, market: NormalizedMarket) -> list[OpportunityLeg]:
        pairs = zip(market.outcomes, market.token_ids, strict=False)
        return [
            OpportunityLeg(
                market_id=market.market_id,
                question=market.question,
                outcome=outcome,
                token_id=token_id,
                best_ask=None,
                average_fill_price=None,
                quantity=None,
                fee_bps=None,
            )
            for outcome, token_id in pairs
        ]

    def _placeholder_legs_from_markets(
        self, markets: list[NormalizedMarket]
    ) -> list[OpportunityLeg]:
        legs: list[OpportunityLeg] = []
        for market in markets:
            yes_index = self._yes_index(market.outcomes)
            if yes_index is None or yes_index >= len(market.token_ids):
                continue
            legs.append(
                OpportunityLeg(
                    market_id=market.market_id,
                    question=market.question,
                    outcome=market.outcomes[yes_index],
                    token_id=market.token_ids[yes_index],
                    best_ask=None,
                    average_fill_price=None,
                    quantity=None,
                    fee_bps=None,
                )
            )
        return legs

    def _placeholder_summary(
        self,
        *,
        spec: _LegSpec,
        books_by_token: dict[str, NormalizedBook],
        fee_rates_by_token: dict[str, NormalizedFeeRate],
    ) -> LegFillSummary:
        book = books_by_token.get(spec.token_id)
        fee_rate = fee_rates_by_token.get(spec.token_id)
        return LegFillSummary(
            market_id=spec.market_id,
            question=spec.question,
            outcome=spec.outcome,
            token_id=spec.token_id,
            best_ask=book.best_ask if book is not None else None,
            quantity=None,
            average_fill_price=None,
            fee_bps=fee_rate.base_fee_bps if fee_rate is not None else None,
        )

    def _sort_key(self, candidate: OpportunityCandidate) -> tuple[object, ...]:
        status_rank = 0 if candidate.status == "accepted" else 1
        net_edge = (
            candidate.net_edge_cents if candidate.net_edge_cents is not None else Decimal("-1")
        )
        gross_edge = (
            candidate.gross_edge_cents if candidate.gross_edge_cents is not None else Decimal("-1")
        )
        capacity = (
            candidate.capacity_shares_or_notional
            if candidate.capacity_shares_or_notional is not None
            else Decimal("-1")
        )
        token_ids = tuple(leg.token_id for leg in candidate.legs)
        return (
            status_rank,
            -net_edge,
            -gross_edge,
            -capacity,
            candidate.event_slug,
            candidate.opportunity_type,
            token_ids,
        )

    def _to_cents(self, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value * _CENTS

    def _yes_index(self, outcomes: list[str]) -> int | None:
        for index, outcome in enumerate(outcomes):
            if outcome.strip().lower() == "yes":
                return index
        return None
