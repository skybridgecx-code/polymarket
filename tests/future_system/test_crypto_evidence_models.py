"""Model validation tests for future_system.crypto_evidence contracts."""

from __future__ import annotations

import pytest
from future_system.crypto_evidence.models import CryptoProxyEvidence, ThemeCryptoEvidencePacket
from pydantic import ValidationError


def test_crypto_evidence_models_accept_valid_payloads() -> None:
    proxy = CryptoProxyEvidence.model_validate(
        {
            "symbol": "BTC-PERP",
            "market_type": "perp",
            "exchange": "deribit",
            "role": "primary_proxy",
            "direction_if_theme_up": "up",
            "last_price": 70500.0,
            "mid_price": 70500.0,
            "funding_rate": -0.0005,
            "open_interest": 12000000.0,
            "liquidity_score": 0.9,
            "freshness_score": 0.8,
            "flags": [],
            "is_primary": True,
        }
    )
    packet = ThemeCryptoEvidencePacket.model_validate(
        {
            "theme_id": "theme_btc",
            "primary_symbol": "BTC-PERP",
            "proxy_evidence": [proxy.model_dump()],
            "matched_symbols": ["BTC-PERP"],
            "liquidity_score": 0.9,
            "freshness_score": 0.8,
            "coverage_score": 1.0,
            "flags": [],
            "explanation": "Deterministic crypto evidence packet.",
        }
    )

    assert proxy.role == "primary_proxy"
    assert packet.primary_symbol == "BTC-PERP"
    assert packet.coverage_score == 1.0


def test_crypto_evidence_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        CryptoProxyEvidence.model_validate(
            {
                "symbol": "BTC-USD",
                "market_type": "spot",
                "exchange": "deribit",
                "role": "confirmation_proxy",
                "direction_if_theme_up": "mixed",
                "last_price": 70000.0,
                "mid_price": 70000.0,
                "funding_rate": None,
                "open_interest": None,
                "liquidity_score": 1.1,
                "freshness_score": 0.8,
                "flags": [],
                "is_primary": False,
            }
        )

    with pytest.raises(ValidationError):
        ThemeCryptoEvidencePacket.model_validate(
            {
                "theme_id": "theme_bad",
                "primary_symbol": "BTC-USD",
                "proxy_evidence": [],
                "matched_symbols": ["BTC-USD"],
                "liquidity_score": 0.7,
                "freshness_score": 0.8,
                "coverage_score": -0.1,
                "flags": [],
                "explanation": "Invalid score payload.",
            }
        )


def test_crypto_evidence_models_enforce_required_fields() -> None:
    with pytest.raises(ValidationError):
        CryptoProxyEvidence.model_validate(
            {
                "symbol": "",
                "market_type": "spot",
                "exchange": "deribit",
                "role": "context_only",
                "direction_if_theme_up": "unknown",
                "last_price": 10.0,
                "mid_price": 10.0,
                "funding_rate": None,
                "open_interest": None,
                "liquidity_score": 0.5,
                "freshness_score": 0.5,
                "flags": [],
                "is_primary": False,
            }
        )

    with pytest.raises(ValidationError):
        ThemeCryptoEvidencePacket.model_validate(
            {
                "theme_id": "   ",
                "primary_symbol": None,
                "proxy_evidence": [],
                "matched_symbols": [],
                "liquidity_score": 0.5,
                "freshness_score": 0.5,
                "coverage_score": 0.0,
                "flags": [],
                "explanation": "Missing theme id.",
            }
        )

