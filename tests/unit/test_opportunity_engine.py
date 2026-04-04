from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from polymarket_arb.ingest.normalize import normalize_books, normalize_events, normalize_fee_rates
from polymarket_arb.models.raw import RawClobBook, RawClobFeeRate, RawGammaEvent
from polymarket_arb.opportunities.engine import OpportunityEngine
from polymarket_arb.opportunities.fees import fee_amount_for_buy_shares


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_candidates() -> list[dict[str, object]]:
    fixture_path = Path("tests/fixtures/scenarios/phase2_opportunities.json")
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)

    fetched_at = datetime(2026, 4, 4, tzinfo=UTC)

    raw_events = [
        RawGammaEvent(source="gamma.events", fetched_at=fetched_at, payload=item)
        for item in payload["events"]
    ]
    raw_books = [
        RawClobBook(
            source="clob.book",
            fetched_at=fetched_at,
            token_id=token_id,
            payload=book_payload,
        )
        for token_id, book_payload in payload["books"].items()
    ]
    raw_fee_rates = [
        RawClobFeeRate(
            source="clob.fee_rate",
            fetched_at=fetched_at,
            token_id=token_id,
            payload=fee_payload,
        )
        for token_id, fee_payload in payload["fee_rates"].items()
    ]

    events = normalize_events(raw_events)
    books_by_token = {book.token_id: book for book in normalize_books(raw_books)}
    fee_rates_by_token = {
        fee_rate.token_id: fee_rate for fee_rate in normalize_fee_rates(raw_fee_rates)
    }

    candidates = OpportunityEngine().build_candidates(
        events=events,
        books_by_token=books_by_token,
        fee_rates_by_token=fee_rates_by_token,
    )
    return [candidate.to_output() for candidate in candidates]


def _candidate_by_event_and_type(
    candidates: list[dict[str, object]],
    *,
    event_slug: str,
    opportunity_type: str,
) -> dict[str, object]:
    for candidate in candidates:
        if (
            candidate["event_slug"] == event_slug
            and candidate["opportunity_type"] == opportunity_type
            and candidate["status"] == "accepted"
        ):
            return candidate
    raise AssertionError(f"Missing accepted candidate for {event_slug=} {opportunity_type=}")


def _rejected_candidate_by_event_and_reason(
    candidates: list[dict[str, object]],
    *,
    event_slug: str,
    rejection_reason: str,
) -> dict[str, object]:
    for candidate in candidates:
        if (
            candidate["event_slug"] == event_slug
            and candidate["status"] == "rejected"
            and candidate["rejection_reason"] == rejection_reason
        ):
            return candidate
    raise AssertionError(f"Missing rejected candidate for {event_slug=} {rejection_reason=}")


def test_fee_amount_for_buy_shares_uses_documented_formula() -> None:
    fee = fee_amount_for_buy_shares(
        shares=Decimal("25"),
        price=Decimal("0.46"),
        base_fee_bps=100,
    )
    assert str(fee) == "0.06210"


def test_opportunity_engine_ranks_fee_aware_candidates_and_limits_capacity_by_liquidity() -> None:
    candidates = _load_candidates()

    assert candidates[0]["event_slug"] == "btc-range-april-2026"
    assert candidates[0]["opportunity_type"] == "neg_risk_basket"
    assert candidates[0]["status"] == "accepted"

    neg_risk = _candidate_by_event_and_type(
        candidates,
        event_slug="btc-range-april-2026",
        opportunity_type="neg_risk_basket",
    )
    assert neg_risk["gross_edge_cents"] == "3880"
    assert neg_risk["estimated_fee_cents"] == "0"
    assert neg_risk["net_edge_cents"] == "3880"
    assert neg_risk["capacity_shares_or_notional"] == "120"
    assert "Basket uses 2 neg-risk Yes legs" in str(neg_risk["explanation"])

    complement = _candidate_by_event_and_type(
        candidates,
        event_slug="fed-hike-june-2026",
        opportunity_type="binary_complement",
    )
    assert complement["gross_edge_cents"] == "105"
    assert complement["estimated_fee_cents"] == "14.948"
    assert complement["net_edge_cents"] == "90.052"
    assert complement["capacity_shares_or_notional"] == "30"
    assert "next marginal bundle costs" in str(complement["explanation"])


def test_opportunity_engine_preserves_rejections_with_explicit_reasons() -> None:
    candidates = _load_candidates()

    no_gross_edge = _rejected_candidate_by_event_and_reason(
        candidates,
        event_slug="btc-range-april-2026",
        rejection_reason="no_gross_edge",
    )
    assert no_gross_edge["gross_edge_cents"] == "0"
    assert "does not leave a positive net edge" in str(no_gross_edge["explanation"])

    missing_fee_rate = _rejected_candidate_by_event_and_reason(
        candidates,
        event_slug="oil-100-july-2026",
        rejection_reason="missing_fee_rate",
    )
    assert missing_fee_rate["gross_edge_cents"] is None
    assert "fee-rate data was unavailable" in str(missing_fee_rate["explanation"])

    insufficient_liquidity = _rejected_candidate_by_event_and_reason(
        candidates,
        event_slug="eth-etf-approval-2026",
        rejection_reason="insufficient_liquidity",
    )
    assert insufficient_liquidity["estimated_fee_cents"] is None
    assert "displayed asks were missing" in str(insufficient_liquidity["explanation"])
