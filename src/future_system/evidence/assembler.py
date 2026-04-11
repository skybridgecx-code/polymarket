"""Deterministic assembler for canonical theme evidence packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Any

from future_system.evidence.freshness import compute_freshness_score, is_stale_snapshot
from future_system.evidence.models import (
    EvidenceAssemblyError,
    NormalizedPolymarketMarketState,
    PolymarketMarketEvidence,
    ThemeEvidencePacket,
)
from future_system.evidence.scoring import (
    compute_evidence_score,
    compute_liquidity_score,
    weighted_probability_average,
)
from future_system.theme_graph.models import ThemeLinkPacket


@dataclass(frozen=True)
class _LinkedIdentifiers:
    condition_ids: set[str]
    market_slugs: set[str]
    event_slugs: set[str]


@dataclass(frozen=True)
class _MatchedMarketEvidence:
    state: NormalizedPolymarketMarketState
    evidence: PolymarketMarketEvidence
    condition_id_match: bool


def assemble_theme_evidence_packet(
    *,
    theme_packet: ThemeLinkPacket,
    market_states: Sequence[NormalizedPolymarketMarketState | Mapping[str, Any]],
    reference_time: datetime,
) -> ThemeEvidencePacket:
    """Build one deterministic evidence packet for the linked theme and market states."""

    linked_identifiers = _extract_linked_identifiers(theme_packet)
    normalized_states = [_normalize_market_state(state) for state in market_states]

    matched: list[_MatchedMarketEvidence] = []
    for state in normalized_states:
        match_basis = _match_basis(state=state, linked_identifiers=linked_identifiers)
        if match_basis is None:
            continue

        matched.append(
            _build_market_evidence(
                state=state,
                reference_time=reference_time,
                condition_id_match=match_basis == "condition_id",
            )
        )

    if not matched:
        raise EvidenceAssemblyError(
            f"No provided market states matched linked markets for theme {theme_packet.theme_id!r}."
        )

    primary = _select_primary_market(matched)
    market_evidence = [
        item.evidence.model_copy(update={"is_primary": item is primary}) for item in matched
    ]

    implied_probabilities = [
        item.implied_yes_probability
        for item in market_evidence
        if item.implied_yes_probability is not None
    ]
    implied_weights = [
        item.liquidity_score for item in market_evidence if item.implied_yes_probability is not None
    ]
    aggregate_probability = weighted_probability_average(
        probabilities=implied_probabilities,
        weights=implied_weights,
    )

    packet_liquidity = round(mean(item.liquidity_score for item in market_evidence), 3)
    packet_freshness = round(mean(item.freshness_score for item in market_evidence), 3)
    packet_evidence_score = compute_evidence_score(
        liquidity_score=packet_liquidity,
        freshness_score=packet_freshness,
    )

    packet_flags = sorted(
        {
            flag
            for item in market_evidence
            for flag in item.flags
        }
    )
    if aggregate_probability is None:
        packet_flags.append("no_aggregate_probability")

    primary_market_slug = primary.evidence.market_slug
    aggregate_text = "none" if aggregate_probability is None else f"{aggregate_probability:.3f}"
    explanation = (
        f"Assembled deterministic evidence for theme {theme_packet.theme_id} from "
        f"{len(market_evidence)} linked market snapshots; "
        f"primary_market={primary_market_slug or 'none'}; "
        f"aggregate_yes_probability={aggregate_text}."
    )

    return ThemeEvidencePacket(
        theme_id=theme_packet.theme_id,
        primary_market_slug=primary_market_slug,
        market_evidence=market_evidence,
        aggregate_yes_probability=aggregate_probability,
        liquidity_score=packet_liquidity,
        freshness_score=packet_freshness,
        evidence_score=packet_evidence_score,
        flags=packet_flags,
        explanation=explanation,
    )


def _normalize_market_state(
    value: NormalizedPolymarketMarketState | Mapping[str, Any],
) -> NormalizedPolymarketMarketState:
    if isinstance(value, NormalizedPolymarketMarketState):
        return value
    return NormalizedPolymarketMarketState.model_validate(value)


def _extract_linked_identifiers(theme_packet: ThemeLinkPacket) -> _LinkedIdentifiers:
    return _LinkedIdentifiers(
        condition_ids={
            linked.condition_id
            for linked in theme_packet.matched_polymarket_markets
            if linked.condition_id is not None
        },
        market_slugs={
            linked.market_slug
            for linked in theme_packet.matched_polymarket_markets
            if linked.market_slug is not None
        },
        event_slugs={
            linked.event_slug
            for linked in theme_packet.matched_polymarket_markets
            if linked.event_slug is not None
        },
    )


def _match_basis(
    *,
    state: NormalizedPolymarketMarketState,
    linked_identifiers: _LinkedIdentifiers,
) -> str | None:
    if (
        state.condition_id is not None
        and state.condition_id in linked_identifiers.condition_ids
    ):
        return "condition_id"
    if (
        state.market_slug is not None
        and state.market_slug in linked_identifiers.market_slugs
    ):
        return "market_slug"
    if (
        state.event_slug is not None
        and state.event_slug in linked_identifiers.event_slugs
    ):
        return "event_slug"
    return None


def _build_market_evidence(
    *,
    state: NormalizedPolymarketMarketState,
    reference_time: datetime,
    condition_id_match: bool,
) -> _MatchedMarketEvidence:
    flags: set[str] = set()

    implied_probability = _implied_yes_probability(state)
    if implied_probability is None:
        flags.add("missing_implied_probability")

    spread = _spread(state)
    if spread is None:
        flags.add("missing_book_data")

    if is_stale_snapshot(snapshot_at=state.snapshot_at, reference_time=reference_time):
        flags.add("stale_snapshot")

    if state.condition_id is None and state.market_slug is None:
        flags.add("missing_relevant_identifiers")

    evidence = PolymarketMarketEvidence(
        market_slug=state.market_slug,
        condition_id=state.condition_id,
        implied_yes_probability=implied_probability,
        spread=spread,
        liquidity_score=compute_liquidity_score(
            spread=spread,
            depth_near_mid=state.depth_near_mid,
            volume_24h=state.volume_24h,
        ),
        freshness_score=compute_freshness_score(
            snapshot_at=state.snapshot_at,
            reference_time=reference_time,
        ),
        flags=sorted(flags),
    )
    return _MatchedMarketEvidence(
        state=state,
        evidence=evidence,
        condition_id_match=condition_id_match,
    )


def _implied_yes_probability(state: NormalizedPolymarketMarketState) -> float | None:
    if state.last_price_yes is not None:
        return state.last_price_yes
    if state.yes_bid is None or state.yes_ask is None:
        return None
    return round((state.yes_bid + state.yes_ask) / 2.0, 6)


def _spread(state: NormalizedPolymarketMarketState) -> float | None:
    if state.yes_bid is None or state.yes_ask is None:
        return None
    return round(state.yes_ask - state.yes_bid, 6)


def _select_primary_market(matched: Sequence[_MatchedMarketEvidence]) -> _MatchedMarketEvidence:
    condition_matches = [item for item in matched if item.condition_id_match]
    pool = condition_matches if condition_matches else list(matched)

    return sorted(
        pool,
        key=lambda item: (
            -item.evidence.liquidity_score,
            item.state.market_slug or "",
        ),
    )[0]

