"""Deterministic exact-match symbol filtering helpers for crypto market states."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.crypto_adapter.models import (
    CryptoSymbolFilter,
    NormalizedCryptoMarketState,
    normalize_crypto_symbol,
)


def filter_market_states_by_symbols(
    *,
    market_states: Sequence[NormalizedCryptoMarketState],
    allowed_symbols: Sequence[str] | None,
) -> list[NormalizedCryptoMarketState]:
    """Filter normalized states by exact normalized symbol, preserving input order."""

    if not allowed_symbols:
        return list(market_states)

    symbol_filter = CryptoSymbolFilter(symbols=list(allowed_symbols))
    allowed = set(symbol_filter.symbols)
    return [state for state in market_states if state.symbol in allowed]


def normalize_symbol_filters(symbols: Sequence[str] | None) -> list[str]:
    """Normalize symbol filter inputs in deterministic uppercase dash format."""

    if not symbols:
        return []
    return [normalize_crypto_symbol(symbol) for symbol in symbols]

