"""Deterministic crypto adapter boundary for fixture-based normalization."""

from future_system.crypto_adapter.filters import (
    filter_market_states_by_symbols,
    normalize_symbol_filters,
)
from future_system.crypto_adapter.models import (
    CryptoAdapterError,
    CryptoAdapterParseResult,
    CryptoMarketStatus,
    CryptoMarketType,
    CryptoSource,
    CryptoSymbolFilter,
    NormalizedCryptoMarketState,
    normalize_crypto_symbol,
)
from future_system.crypto_adapter.parser import FixtureCryptoAdapter, parse_crypto_market_snapshots
from future_system.crypto_adapter.protocol import CryptoAdapterProtocol

__all__ = [
    "CryptoAdapterError",
    "CryptoAdapterParseResult",
    "CryptoAdapterProtocol",
    "CryptoMarketStatus",
    "CryptoMarketType",
    "CryptoSource",
    "CryptoSymbolFilter",
    "FixtureCryptoAdapter",
    "NormalizedCryptoMarketState",
    "filter_market_states_by_symbols",
    "normalize_crypto_symbol",
    "normalize_symbol_filters",
    "parse_crypto_market_snapshots",
]

