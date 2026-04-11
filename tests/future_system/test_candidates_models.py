"""Model validation tests for future_system.candidates contracts."""

from __future__ import annotations

import pytest
from future_system.candidates.models import CandidateSignalPacket
from pydantic import ValidationError


def test_candidate_models_accept_valid_payloads() -> None:
    packet = CandidateSignalPacket.model_validate(
        {
            "theme_id": "theme_candidate_models",
            "title": None,
            "posture": "candidate",
            "candidate_score": 0.74,
            "confidence_score": 0.69,
            "conflict_score": 0.21,
            "alignment": "aligned",
            "primary_market_slug": "candidate-market",
            "primary_symbol": "btc-perp",
            "reason_codes": [
                "strong_cross_market_alignment",
                "strong_cross_market_alignment",
            ],
            "flags": ["cross_market_conflict", "cross_market_conflict"],
            "explanation": "Deterministic candidate signal.",
        }
    )

    assert packet.posture == "candidate"
    assert packet.primary_symbol == "BTC-PERP"
    assert packet.reason_codes == ["strong_cross_market_alignment"]
    assert packet.flags == ["cross_market_conflict"]


def test_candidate_models_reject_invalid_bounded_scores() -> None:
    with pytest.raises(ValidationError):
        CandidateSignalPacket.model_validate(
            {
                "theme_id": "theme_bad_scores",
                "title": None,
                "posture": "watch",
                "candidate_score": 1.2,
                "confidence_score": 0.6,
                "conflict_score": 0.3,
                "alignment": "weakly_aligned",
                "primary_market_slug": None,
                "primary_symbol": None,
                "reason_codes": [],
                "flags": [],
                "explanation": "Invalid candidate score.",
            }
        )


def test_candidate_models_reject_invalid_posture() -> None:
    with pytest.raises(ValidationError):
        CandidateSignalPacket.model_validate(
            {
                "theme_id": "theme_bad_posture",
                "title": None,
                "posture": "promote",
                "candidate_score": 0.7,
                "confidence_score": 0.7,
                "conflict_score": 0.2,
                "alignment": "aligned",
                "primary_market_slug": None,
                "primary_symbol": None,
                "reason_codes": [],
                "flags": [],
                "explanation": "Invalid posture literal.",
            }
        )
