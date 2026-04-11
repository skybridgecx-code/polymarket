"""Model validation tests for future_system.comparison contracts."""

from __future__ import annotations

import pytest
from future_system.comparison.models import EvidenceFamilySummary, ThemeComparisonPacket
from pydantic import ValidationError


def test_comparison_models_accept_valid_payloads() -> None:
    polymarket_summary = EvidenceFamilySummary.model_validate(
        {
            "family": "polymarket",
            "direction": "bullish",
            "strength_score": 0.8,
            "freshness_score": 0.9,
            "liquidity_score": 0.75,
            "coverage_score": None,
            "flags": [],
        }
    )
    crypto_summary = EvidenceFamilySummary.model_validate(
        {
            "family": "crypto",
            "direction": "mixed",
            "strength_score": 0.6,
            "freshness_score": 0.7,
            "liquidity_score": 0.65,
            "coverage_score": 0.8,
            "flags": [],
        }
    )
    packet = ThemeComparisonPacket.model_validate(
        {
            "theme_id": "theme_models",
            "polymarket_summary": polymarket_summary.model_dump(),
            "crypto_summary": crypto_summary.model_dump(),
            "alignment": "weakly_aligned",
            "agreement_score": 0.61,
            "confidence_score": 0.58,
            "flags": [],
            "explanation": "Deterministic comparison packet.",
        }
    )

    assert packet.alignment == "weakly_aligned"
    assert packet.polymarket_summary.direction == "bullish"
    assert packet.crypto_summary.direction == "mixed"


def test_comparison_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        EvidenceFamilySummary.model_validate(
            {
                "family": "polymarket",
                "direction": "bullish",
                "strength_score": 1.2,
                "freshness_score": 0.9,
                "liquidity_score": 0.8,
                "coverage_score": None,
                "flags": [],
            }
        )

    with pytest.raises(ValidationError):
        ThemeComparisonPacket.model_validate(
            {
                "theme_id": "theme_bad",
                "polymarket_summary": {
                    "family": "polymarket",
                    "direction": "bullish",
                    "strength_score": 0.7,
                    "freshness_score": 0.8,
                    "liquidity_score": 0.7,
                    "coverage_score": None,
                    "flags": [],
                },
                "crypto_summary": {
                    "family": "crypto",
                    "direction": "bearish",
                    "strength_score": 0.7,
                    "freshness_score": 0.8,
                    "liquidity_score": 0.7,
                    "coverage_score": 0.8,
                    "flags": [],
                },
                "alignment": "conflicted",
                "agreement_score": -0.01,
                "confidence_score": 0.5,
                "flags": [],
                "explanation": "Invalid agreement score.",
            }
        )


def test_comparison_models_reject_invalid_alignment_and_direction() -> None:
    with pytest.raises(ValidationError):
        EvidenceFamilySummary.model_validate(
            {
                "family": "crypto",
                "direction": "positive",
                "strength_score": 0.7,
                "freshness_score": 0.7,
                "liquidity_score": 0.7,
                "coverage_score": 0.8,
                "flags": [],
            }
        )

    with pytest.raises(ValidationError):
        ThemeComparisonPacket.model_validate(
            {
                "theme_id": "theme_bad_alignment",
                "polymarket_summary": {
                    "family": "polymarket",
                    "direction": "bullish",
                    "strength_score": 0.7,
                    "freshness_score": 0.8,
                    "liquidity_score": 0.7,
                    "coverage_score": None,
                    "flags": [],
                },
                "crypto_summary": {
                    "family": "crypto",
                    "direction": "bullish",
                    "strength_score": 0.7,
                    "freshness_score": 0.8,
                    "liquidity_score": 0.7,
                    "coverage_score": 0.8,
                    "flags": [],
                },
                "alignment": "partially_aligned",
                "agreement_score": 0.7,
                "confidence_score": 0.7,
                "flags": [],
                "explanation": "Invalid alignment literal.",
            }
        )

