"""Validation tests for future_system.crypto_adapter models."""

from __future__ import annotations

import pytest
from future_system.crypto_adapter.models import NormalizedCryptoMarketState
from pydantic import ValidationError


def test_normalized_crypto_market_state_accepts_valid_payload() -> None:
    state = NormalizedCryptoMarketState.model_validate(_valid_payload())

    assert state.exchange == "deribit"
    assert state.symbol == "BTC-USD"
    assert state.base_asset == "BTC"
    assert state.quote_asset == "USD"
    assert state.market_type == "spot"


def test_negative_numeric_fields_are_rejected() -> None:
    negative_last = _valid_payload()
    negative_last["last_price"] = -1.0

    with pytest.raises(ValidationError):
        NormalizedCryptoMarketState.model_validate(negative_last)

    negative_volume = _valid_payload()
    negative_volume["volume_24h"] = -100.0

    with pytest.raises(ValidationError):
        NormalizedCryptoMarketState.model_validate(negative_volume)


def test_bid_ask_ordering_is_enforced() -> None:
    invalid = _valid_payload()
    invalid["bid_price"] = 100.0
    invalid["ask_price"] = 99.0

    with pytest.raises(ValidationError):
        NormalizedCryptoMarketState.model_validate(invalid)


def test_required_string_fields_are_enforced() -> None:
    invalid_exchange = _valid_payload()
    invalid_exchange["exchange"] = "   "

    with pytest.raises(ValidationError):
        NormalizedCryptoMarketState.model_validate(invalid_exchange)

    invalid_symbol = _valid_payload()
    invalid_symbol["symbol"] = ""

    with pytest.raises(ValidationError):
        NormalizedCryptoMarketState.model_validate(invalid_symbol)


def _valid_payload() -> dict[str, object]:
    return {
        "source": "fixture",
        "exchange": "deribit",
        "symbol": "BTC-USD",
        "base_asset": "btc",
        "quote_asset": "usd",
        "market_type": "spot",
        "last_price": 70000.0,
        "bid_price": 69990.0,
        "ask_price": 70010.0,
        "mid_price": 70000.0,
        "volume_24h": 12345.0,
        "open_interest": 10000.0,
        "funding_rate": -0.001,
        "snapshot_at": "2026-02-01T12:00:00Z",
        "status": "active",
    }

