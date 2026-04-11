"""Deterministic assembler for theme-linked normalized crypto evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Any

from future_system.crypto_adapter.models import NormalizedCryptoMarketState, normalize_crypto_symbol
from future_system.crypto_evidence.models import (
    CryptoEvidenceAssemblyError,
    CryptoProxyEvidence,
    ThemeCryptoEvidencePacket,
)
from future_system.crypto_evidence.scoring import (
    compute_crypto_coverage_score,
    compute_crypto_freshness_score,
    compute_crypto_liquidity_score,
    is_crypto_stale,
)
from future_system.theme_graph.models import AssetThemeLink, ThemeLinkPacket

_CRYPTO_ASSET_TYPES = frozenset({"spot", "perp"})
_ROLE_PRIORITY = {
    "primary_proxy": 0,
    "confirmation_proxy": 1,
    "hedge_proxy": 2,
    "context_only": 3,
}


@dataclass(frozen=True)
class _MatchedProxy:
    state: NormalizedCryptoMarketState
    linked_asset: AssetThemeLink
    evidence: CryptoProxyEvidence


def assemble_theme_crypto_evidence_packet(
    *,
    theme_packet: ThemeLinkPacket,
    crypto_states: Sequence[NormalizedCryptoMarketState | Mapping[str, Any]],
    reference_time: datetime,
) -> ThemeCryptoEvidencePacket:
    """Build deterministic crypto evidence packet from linked theme assets and states."""

    linked_assets = _extract_linked_crypto_assets(theme_packet)
    if not linked_assets:
        raise CryptoEvidenceAssemblyError(
            f"No crypto-linked assets for theme {theme_packet.theme_id!r}."
        )

    normalized_states = [_normalize_state(state) for state in crypto_states]
    matched_proxies: list[_MatchedProxy] = []
    for state in normalized_states:
        linked_asset = _select_linked_asset_for_state(state=state, linked_assets=linked_assets)
        if linked_asset is None:
            continue
        matched_proxies.append(
            _build_proxy_evidence(
                state=state,
                linked_asset=linked_asset,
                reference_time=reference_time,
            )
        )

    if not matched_proxies:
        raise CryptoEvidenceAssemblyError(
            f"No linked crypto market states matched theme {theme_packet.theme_id!r}."
        )

    primary = _select_primary_proxy(matched_proxies)
    proxy_evidence = [
        item.evidence.model_copy(update={"is_primary": item is primary}) for item in matched_proxies
    ]

    matched_symbols = _unique_in_order(item.symbol for item in proxy_evidence)
    linked_symbols = _unique_in_order(_normalized_link_symbol(asset) for asset in linked_assets)
    matched_linked_symbols = [
        linked_symbol
        for linked_symbol in linked_symbols
        if any(_linked_symbol_matches_state(linked_symbol, state) for state in normalized_states)
    ]
    coverage_score = compute_crypto_coverage_score(
        matched_count=len(matched_linked_symbols),
        linked_count=len(linked_symbols),
    )

    packet_liquidity = round(mean(item.liquidity_score for item in proxy_evidence), 3)
    packet_freshness = round(mean(item.freshness_score for item in proxy_evidence), 3)

    flags = {flag for item in proxy_evidence for flag in item.flags}
    if coverage_score < 1.0:
        flags.add("incomplete_linked_symbol_coverage")
    if any("stale_snapshot" in item.flags for item in proxy_evidence):
        flags.add("stale_snapshot")
    if any("missing_price_data" in item.flags for item in proxy_evidence):
        flags.add("missing_price_data")
    if any("low_liquidity" in item.flags for item in proxy_evidence):
        flags.add("low_liquidity")

    primary_symbol = primary.evidence.symbol
    ordered_flags = sorted(flags)
    flag_text = "none" if not ordered_flags else ",".join(ordered_flags)
    explanation = (
        f"Matched proxies={len(proxy_evidence)} linked_symbols={len(linked_symbols)}; "
        f"primary_symbol={primary_symbol}; "
        f"liquidity_score={packet_liquidity:.3f}; "
        f"freshness_score={packet_freshness:.3f}; "
        f"coverage_score={coverage_score:.3f}; "
        f"flags={flag_text}."
    )

    return ThemeCryptoEvidencePacket(
        theme_id=theme_packet.theme_id,
        primary_symbol=primary_symbol,
        proxy_evidence=proxy_evidence,
        matched_symbols=matched_symbols,
        liquidity_score=packet_liquidity,
        freshness_score=packet_freshness,
        coverage_score=coverage_score,
        flags=ordered_flags,
        explanation=explanation,
    )


def _normalize_state(
    value: NormalizedCryptoMarketState | Mapping[str, Any],
) -> NormalizedCryptoMarketState:
    if isinstance(value, NormalizedCryptoMarketState):
        return value
    return NormalizedCryptoMarketState.model_validate(value)


def _extract_linked_crypto_assets(theme_packet: ThemeLinkPacket) -> list[AssetThemeLink]:
    return [
        asset for asset in theme_packet.matched_assets if asset.asset_type in _CRYPTO_ASSET_TYPES
    ]


def _select_linked_asset_for_state(
    *,
    state: NormalizedCryptoMarketState,
    linked_assets: Sequence[AssetThemeLink],
) -> AssetThemeLink | None:
    candidates = [asset for asset in linked_assets if _linked_asset_matches_state(asset, state)]
    if not candidates:
        return None

    def _sort_key(asset: AssetThemeLink) -> tuple[int, int, str]:
        return (
            0 if _is_full_symbol(asset.symbol) else 1,
            _ROLE_PRIORITY[asset.role],
            _normalized_link_symbol(asset),
        )

    return sorted(candidates, key=_sort_key)[0]


def _linked_asset_matches_state(asset: AssetThemeLink, state: NormalizedCryptoMarketState) -> bool:
    linked_symbol = _normalized_link_symbol(asset)
    return _linked_symbol_matches_state(linked_symbol, state)


def _linked_symbol_matches_state(linked_symbol: str, state: NormalizedCryptoMarketState) -> bool:
    if _is_full_symbol(linked_symbol):
        return state.symbol == linked_symbol
    return state.base_asset == linked_symbol


def _build_proxy_evidence(
    *,
    state: NormalizedCryptoMarketState,
    linked_asset: AssetThemeLink,
    reference_time: datetime,
) -> _MatchedProxy:
    freshness_score = compute_crypto_freshness_score(
        snapshot_at=state.snapshot_at,
        reference_time=reference_time,
    )
    liquidity_score = compute_crypto_liquidity_score(
        market_type=state.market_type,
        bid_price=state.bid_price,
        ask_price=state.ask_price,
        volume_24h=state.volume_24h,
        open_interest=state.open_interest,
    )

    flags: set[str] = set()
    if is_crypto_stale(snapshot_at=state.snapshot_at, reference_time=reference_time):
        flags.add("stale_snapshot")
    if state.last_price is None and state.mid_price is None:
        flags.add("missing_price_data")
    if liquidity_score < 0.4:
        flags.add("low_liquidity")

    evidence = CryptoProxyEvidence(
        symbol=state.symbol,
        market_type=state.market_type,
        exchange=state.exchange,
        role=linked_asset.role,
        direction_if_theme_up=linked_asset.direction_if_theme_up,
        last_price=state.last_price,
        mid_price=state.mid_price,
        funding_rate=state.funding_rate,
        open_interest=state.open_interest,
        liquidity_score=liquidity_score,
        freshness_score=freshness_score,
        flags=sorted(flags),
    )
    return _MatchedProxy(state=state, linked_asset=linked_asset, evidence=evidence)


def _select_primary_proxy(matched_proxies: Sequence[_MatchedProxy]) -> _MatchedProxy:
    return sorted(
        matched_proxies,
        key=lambda item: (
            _ROLE_PRIORITY[item.evidence.role],
            -item.evidence.liquidity_score,
            item.evidence.symbol,
        ),
    )[0]


def _normalized_link_symbol(asset: AssetThemeLink) -> str:
    return normalize_crypto_symbol(asset.symbol)


def _is_full_symbol(symbol: str) -> bool:
    return "-" in symbol


def _unique_in_order(values: Sequence[str] | Any) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered

