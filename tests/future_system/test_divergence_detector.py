"""Behavior tests for deterministic divergence detection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.divergence.detector import detect_theme_divergence
from future_system.divergence.models import DivergenceDetectionError
from future_system.evidence.models import ThemeEvidencePacket

_FIXTURE_PATH = Path("tests/fixtures/future_system/divergence/theme_evidence_packets.json")


def test_aligned_packet_produces_aligned_posture() -> None:
    aligned_packet = _packets_by_case()["aligned"]

    divergence = detect_theme_divergence(evidence_packet=aligned_packet)

    assert divergence.posture == "aligned"
    assert divergence.dispersion_score == 0.022
    assert divergence.flags == []


def test_moderate_disagreement_produces_mixed_posture() -> None:
    mixed_packet = _packets_by_case()["mixed"]

    divergence = detect_theme_divergence(evidence_packet=mixed_packet)

    assert divergence.posture == "mixed"
    assert divergence.dispersion_score == 0.333
    assert "missing_probability_inputs" in divergence.flags
    assert "stale_evidence" in divergence.flags
    assert "weak_liquidity" in divergence.flags


def test_high_disagreement_produces_conflicted_posture() -> None:
    conflicted_packet = _packets_by_case()["conflicted"]

    divergence = detect_theme_divergence(evidence_packet=conflicted_packet)

    assert divergence.posture == "conflicted"
    assert divergence.dispersion_score == 0.844
    assert "high_internal_dispersion" in divergence.flags


def test_missing_aggregate_produces_insufficient_posture() -> None:
    insufficient_packet = _packets_by_case()["insufficient"]

    divergence = detect_theme_divergence(evidence_packet=insufficient_packet)

    assert divergence.posture == "insufficient"
    assert "no_aggregate_probability" in divergence.flags


def test_single_usable_market_produces_insufficient_posture() -> None:
    packet = ThemeEvidencePacket.model_validate(
        {
            "theme_id": "single_usable",
            "primary_market_slug": "single-usable-primary",
            "market_evidence": [
                {
                    "market_slug": "single-usable-primary",
                    "condition_id": "0xsingle1",
                    "implied_yes_probability": 0.62,
                    "spread": 0.05,
                    "liquidity_score": 0.71,
                    "freshness_score": 0.82,
                    "flags": [],
                    "is_primary": True,
                },
                {
                    "market_slug": "single-usable-secondary",
                    "condition_id": "0xsingle2",
                    "implied_yes_probability": None,
                    "spread": None,
                    "liquidity_score": 0.68,
                    "freshness_score": 0.78,
                    "flags": ["missing_implied_probability"],
                    "is_primary": False,
                },
            ],
            "aggregate_yes_probability": 0.62,
            "liquidity_score": 0.7,
            "freshness_score": 0.8,
            "evidence_score": 0.74,
            "flags": [],
            "explanation": "Single usable fixture.",
        }
    )

    divergence = detect_theme_divergence(evidence_packet=packet)

    assert divergence.posture == "insufficient"
    assert "single_usable_market" in divergence.flags


def test_market_disagreement_entries_are_deterministic() -> None:
    conflicted_packet = _packets_by_case()["conflicted"]

    divergence_a = detect_theme_divergence(evidence_packet=conflicted_packet)
    divergence_b = detect_theme_divergence(evidence_packet=conflicted_packet)

    assert divergence_a.model_dump() == divergence_b.model_dump()
    severities = [entry.severity for entry in divergence_a.market_disagreements]
    assert severities == ["high", "high", "low"]


def test_explanation_string_is_deterministic() -> None:
    aligned_packet = _packets_by_case()["aligned"]

    divergence = detect_theme_divergence(evidence_packet=aligned_packet)

    assert divergence.explanation == (
        "aggregate_yes_probability=0.600; "
        "usable_markets=3/3; "
        "posture=aligned; "
        "flags=none."
    )


def test_detector_raises_for_empty_market_evidence() -> None:
    packet = ThemeEvidencePacket.model_validate(
        {
            "theme_id": "empty_markets",
            "primary_market_slug": None,
            "market_evidence": [],
            "aggregate_yes_probability": 0.5,
            "liquidity_score": 0.6,
            "freshness_score": 0.7,
            "evidence_score": 0.64,
            "flags": [],
            "explanation": "No markets.",
        }
    )

    with pytest.raises(DivergenceDetectionError):
        detect_theme_divergence(evidence_packet=packet)


def _packets_by_case() -> dict[str, ThemeEvidencePacket]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: ThemeEvidencePacket.model_validate(entry["packet"])
        for entry in payload
    }

