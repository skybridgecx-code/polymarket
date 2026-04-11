"""Scoring tests for deterministic Polymarket-vs-crypto comparison helpers."""

from __future__ import annotations

from future_system.comparison.scoring import (
    classify_alignment,
    compute_agreement_score,
    compute_comparison_confidence_score,
    derive_crypto_direction,
    derive_polymarket_direction,
)
from future_system.crypto_evidence.models import CryptoProxyEvidence


def test_polymarket_direction_thresholds_are_deterministic() -> None:
    assert derive_polymarket_direction(aggregate_yes_probability=0.56) == "bullish"
    assert derive_polymarket_direction(aggregate_yes_probability=0.44) == "bearish"
    assert derive_polymarket_direction(aggregate_yes_probability=0.50) == "mixed"
    assert derive_polymarket_direction(aggregate_yes_probability=None) == "unknown"


def test_crypto_direction_derivation_is_deterministic_for_proxy_mixes() -> None:
    bullish = derive_crypto_direction(
        proxy_evidence=[_proxy("up"), _proxy("up", role="hedge_proxy")]
    )
    bearish = derive_crypto_direction(
        proxy_evidence=[_proxy("down"), _proxy("down", role="confirmation_proxy")]
    )
    mixed = derive_crypto_direction(
        proxy_evidence=[_proxy("up"), _proxy("down", role="primary_proxy")]
    )
    unknown = derive_crypto_direction(
        proxy_evidence=[_proxy("up", last_price=None, mid_price=None)]
    )

    assert bullish == "bullish"
    assert bearish == "bearish"
    assert mixed == "mixed"
    assert unknown == "unknown"


def test_agreement_and_confidence_scores_are_bounded() -> None:
    agreement = compute_agreement_score(
        polymarket_direction="bullish",
        crypto_direction="bullish",
        polymarket_strength=1.5,
        crypto_strength=-0.2,
    )
    confidence = compute_comparison_confidence_score(
        agreement_score=agreement,
        polymarket_strength=2.0,
        crypto_strength=-2.0,
        flags=["weak_crypto_coverage", "stale_crypto_evidence"],
    )

    assert 0.0 <= agreement <= 1.0
    assert 0.0 <= confidence <= 1.0


def test_alignment_thresholds_are_deterministic() -> None:
    aligned = classify_alignment(
        polymarket_direction="bullish",
        crypto_direction="bullish",
        agreement_score=0.875,
        confidence_score=0.825,
        polymarket_strength=0.8,
        crypto_strength=0.7,
    )
    weakly_aligned = classify_alignment(
        polymarket_direction="bullish",
        crypto_direction="mixed",
        agreement_score=0.495,
        confidence_score=0.45,
        polymarket_strength=0.75,
        crypto_strength=0.65,
    )
    conflicted = classify_alignment(
        polymarket_direction="bullish",
        crypto_direction="bearish",
        agreement_score=0.088,
        confidence_score=0.353,
        polymarket_strength=0.8,
        crypto_strength=0.7,
    )
    insufficient = classify_alignment(
        polymarket_direction="unknown",
        crypto_direction="bullish",
        agreement_score=0.0,
        confidence_score=0.2,
        polymarket_strength=0.7,
        crypto_strength=0.7,
    )

    assert aligned == "aligned"
    assert weakly_aligned == "weakly_aligned"
    assert conflicted == "conflicted"
    assert insufficient == "insufficient"


def test_known_scoring_outputs_are_deterministic() -> None:
    agreement_a = compute_agreement_score(
        polymarket_direction="bullish",
        crypto_direction="bullish",
        polymarket_strength=0.8,
        crypto_strength=0.7,
    )
    agreement_b = compute_agreement_score(
        polymarket_direction="bullish",
        crypto_direction="bullish",
        polymarket_strength=0.8,
        crypto_strength=0.7,
    )
    confidence_a = compute_comparison_confidence_score(
        agreement_score=agreement_a,
        polymarket_strength=0.8,
        crypto_strength=0.7,
        flags=[],
    )
    confidence_b = compute_comparison_confidence_score(
        agreement_score=agreement_b,
        polymarket_strength=0.8,
        crypto_strength=0.7,
        flags=[],
    )

    assert agreement_a == agreement_b == 0.875
    assert confidence_a == confidence_b == 0.825


def _proxy(
    direction_if_theme_up: str,
    *,
    role: str = "primary_proxy",
    last_price: float | None = 100.0,
    mid_price: float | None = 100.0,
) -> CryptoProxyEvidence:
    return CryptoProxyEvidence.model_validate(
        {
            "symbol": "BTC-PERP",
            "market_type": "perp",
            "exchange": "deribit",
            "role": role,
            "direction_if_theme_up": direction_if_theme_up,
            "last_price": last_price,
            "mid_price": mid_price,
            "funding_rate": 0.0,
            "open_interest": 1_000_000.0,
            "liquidity_score": 0.8,
            "freshness_score": 0.8,
            "flags": [],
            "is_primary": role == "primary_proxy",
        }
    )
