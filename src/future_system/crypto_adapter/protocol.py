"""Bounded protocol contract for deterministic crypto adapter behavior."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from future_system.crypto_adapter.models import (
    CryptoAdapterParseResult,
    NormalizedCryptoMarketState,
)


@runtime_checkable
class CryptoAdapterProtocol(Protocol):
    """Small adapter contract for parsing and exact symbol filtering."""

    def parse_raw_payload(
        self,
        payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        default_exchange: str | None = None,
    ) -> CryptoAdapterParseResult:
        """Parse raw payload records into normalized crypto market states."""

    def filter_market_states(
        self,
        market_states: Sequence[NormalizedCryptoMarketState],
        *,
        allowed_symbols: Sequence[str] | None,
    ) -> list[NormalizedCryptoMarketState]:
        """Return normalized market states filtered by exact symbol match."""
