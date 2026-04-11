"""Filtering tests for deterministic crypto adapter symbol matching."""

from __future__ import annotations

from future_system.crypto_adapter.filters import (
    filter_market_states_by_symbols,
    normalize_symbol_filters,
)
from future_system.crypto_adapter.models import NormalizedCryptoMarketState


def test_exact_symbol_filter_matches_expected_states() -> None:
    states = _states()

    filtered = filter_market_states_by_symbols(
        market_states=states,
        allowed_symbols=["ETH-USD", "BTC-PERP"],
    )

    assert [state.symbol for state in filtered] == ["ETH-USD", "BTC-PERP"]


def test_unmatched_symbols_return_empty_list() -> None:
    states = _states()

    filtered = filter_market_states_by_symbols(
        market_states=states,
        allowed_symbols=["SOL-USD"],
    )

    assert filtered == []


def test_input_order_is_preserved_after_filtering() -> None:
    states = _states()

    filtered = filter_market_states_by_symbols(
        market_states=states,
        allowed_symbols=["BTC-PERP", "BTC-USD"],
    )

    assert [state.symbol for state in filtered] == ["BTC-USD", "BTC-PERP"]


def test_symbol_normalization_is_deterministic() -> None:
    normalized = normalize_symbol_filters(["eth/usd", " btc_perp ", "BTC-USD"])

    assert normalized == ["ETH-USD", "BTC-PERP", "BTC-USD"]


def _states() -> list[NormalizedCryptoMarketState]:
    return [
        NormalizedCryptoMarketState.model_validate(
            {
                "source": "fixture",
                "exchange": "deribit",
                "symbol": "BTC-USD",
                "base_asset": "BTC",
                "quote_asset": "USD",
                "market_type": "spot",
                "last_price": 70000.0,
                "bid_price": 69990.0,
                "ask_price": 70010.0,
                "mid_price": 70000.0,
                "volume_24h": 15000.0,
                "open_interest": None,
                "funding_rate": None,
                "snapshot_at": "2026-02-01T12:00:00Z",
                "status": "active",
            }
        ),
        NormalizedCryptoMarketState.model_validate(
            {
                "source": "fixture",
                "exchange": "deribit",
                "symbol": "ETH-USD",
                "base_asset": "ETH",
                "quote_asset": "USD",
                "market_type": "spot",
                "last_price": 3800.0,
                "bid_price": 3798.0,
                "ask_price": 3802.0,
                "mid_price": 3800.0,
                "volume_24h": 22000.0,
                "open_interest": None,
                "funding_rate": None,
                "snapshot_at": "2026-02-01T12:00:00Z",
                "status": "active",
            }
        ),
        NormalizedCryptoMarketState.model_validate(
            {
                "source": "fixture",
                "exchange": "deribit",
                "symbol": "BTC-PERP",
                "base_asset": "BTC",
                "quote_asset": "USD",
                "market_type": "perp",
                "last_price": 70100.0,
                "bid_price": 70095.0,
                "ask_price": 70105.0,
                "mid_price": 70100.0,
                "volume_24h": 90000.0,
                "open_interest": 1000000.0,
                "funding_rate": -0.0005,
                "snapshot_at": "2026-02-01T12:00:00Z",
                "status": "active",
            }
        ),
    ]

