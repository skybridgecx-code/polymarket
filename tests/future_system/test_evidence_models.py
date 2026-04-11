"""Validation tests for canonical future_system evidence models."""

from __future__ import annotations

import pytest
from future_system.evidence.models import NormalizedPolymarketMarketState
from pydantic import ValidationError


def test_market_state_accepts_valid_payload() -> None:
    state = NormalizedPolymarketMarketState.model_validate(_valid_market_state_payload())

    assert state.condition_id == "0xvalidcondition"
    assert state.market_slug == "valid-market"
    assert state.last_price_yes == 0.64
    assert state.status == "active"


def test_market_state_rejects_negative_volume_and_depth() -> None:
    invalid_volume = _valid_market_state_payload()
    invalid_volume["volume_24h"] = -1.0

    with pytest.raises(ValidationError):
        NormalizedPolymarketMarketState.model_validate(invalid_volume)

    invalid_depth = _valid_market_state_payload()
    invalid_depth["depth_near_mid"] = -0.5

    with pytest.raises(ValidationError):
        NormalizedPolymarketMarketState.model_validate(invalid_depth)


def test_market_state_rejects_probabilities_outside_unit_interval() -> None:
    too_high = _valid_market_state_payload()
    too_high["yes_bid"] = 1.01

    with pytest.raises(ValidationError):
        NormalizedPolymarketMarketState.model_validate(too_high)

    too_low = _valid_market_state_payload()
    too_low["last_price_yes"] = -0.01

    with pytest.raises(ValidationError):
        NormalizedPolymarketMarketState.model_validate(too_low)


def test_market_state_requires_at_least_one_identifier() -> None:
    invalid = _valid_market_state_payload()
    invalid["condition_id"] = None
    invalid["market_slug"] = None
    invalid["event_slug"] = None

    with pytest.raises(ValidationError):
        NormalizedPolymarketMarketState.model_validate(invalid)


def _valid_market_state_payload() -> dict[str, object]:
    return {
        "market_slug": "valid-market",
        "event_slug": "valid-event",
        "condition_id": "0xvalidcondition",
        "question": "Is the model payload valid?",
        "yes_bid": 0.62,
        "yes_ask": 0.66,
        "no_bid": 0.34,
        "no_ask": 0.38,
        "last_price_yes": 0.64,
        "volume_24h": 25000.0,
        "depth_near_mid": 900.0,
        "snapshot_at": "2026-01-01T00:00:00Z",
        "last_trade_at": "2026-01-01T00:00:00Z",
        "resolution_at": "2026-03-01T00:00:00Z",
        "status": "active",
    }

