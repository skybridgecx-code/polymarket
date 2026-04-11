"""Model validation tests for future_system.divergence contracts."""

from __future__ import annotations

import pytest
from future_system.divergence.models import MarketDisagreement, ThemeDivergencePacket
from pydantic import ValidationError


def test_divergence_models_accept_valid_payloads() -> None:
    disagreement = MarketDisagreement.model_validate(
        {
            "market_slug": "valid-market",
            "condition_id": "0xvalid",
            "implied_yes_probability": 0.57,
            "distance_from_aggregate": 0.03,
            "liquidity_score": 0.72,
            "freshness_score": 0.88,
            "flags": [],
            "severity": "low",
        }
    )
    packet = ThemeDivergencePacket.model_validate(
        {
            "theme_id": "theme_valid",
            "primary_market_slug": "valid-market",
            "aggregate_yes_probability": 0.6,
            "dispersion_score": 0.12,
            "quality_penalty": 0.2,
            "divergence_score": 0.144,
            "posture": "aligned",
            "market_disagreements": [disagreement.model_dump()],
            "flags": [],
            "explanation": "Valid divergence packet.",
        }
    )

    assert disagreement.severity == "low"
    assert packet.posture == "aligned"
    assert packet.market_disagreements[0].distance_from_aggregate == 0.03


def test_divergence_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        MarketDisagreement.model_validate(
            {
                "market_slug": "invalid-market",
                "condition_id": "0xinvalid",
                "implied_yes_probability": 1.2,
                "distance_from_aggregate": 0.05,
                "liquidity_score": 0.7,
                "freshness_score": 0.8,
                "flags": [],
                "severity": "medium",
            }
        )

    with pytest.raises(ValidationError):
        ThemeDivergencePacket.model_validate(
            {
                "theme_id": "theme_invalid",
                "primary_market_slug": "invalid-market",
                "aggregate_yes_probability": 0.5,
                "dispersion_score": 1.01,
                "quality_penalty": 0.2,
                "divergence_score": 0.3,
                "posture": "mixed",
                "market_disagreements": [],
                "flags": [],
                "explanation": "Invalid bounded score.",
            }
        )


def test_divergence_models_reject_invalid_posture_and_severity() -> None:
    with pytest.raises(ValidationError):
        MarketDisagreement.model_validate(
            {
                "market_slug": "bad-severity-market",
                "condition_id": "0xbad",
                "implied_yes_probability": 0.57,
                "distance_from_aggregate": 0.03,
                "liquidity_score": 0.7,
                "freshness_score": 0.8,
                "flags": [],
                "severity": "critical",
            }
        )

    with pytest.raises(ValidationError):
        ThemeDivergencePacket.model_validate(
            {
                "theme_id": "theme_bad_posture",
                "primary_market_slug": "bad-posture-market",
                "aggregate_yes_probability": 0.5,
                "dispersion_score": 0.2,
                "quality_penalty": 0.2,
                "divergence_score": 0.2,
                "posture": "uncertain",
                "market_disagreements": [],
                "flags": [],
                "explanation": "Invalid posture value.",
            }
        )

