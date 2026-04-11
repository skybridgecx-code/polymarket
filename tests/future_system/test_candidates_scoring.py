"""Scoring tests for deterministic candidate signal helpers."""

from __future__ import annotations

from future_system.candidates.scoring import (
    classify_candidate_posture,
    compute_candidate_confidence_score,
    compute_candidate_conflict_score,
    compute_candidate_score,
    derive_candidate_reason_codes,
)


def test_candidate_score_is_bounded_in_unit_interval() -> None:
    score = compute_candidate_score(
        agreement_score=2.0,
        comparison_confidence=-2.0,
        evidence_score=2.0,
        evidence_liquidity=-1.0,
        evidence_freshness=4.0,
        crypto_coverage=-2.0,
        crypto_liquidity=3.0,
        crypto_freshness=3.0,
        divergence_score=3.0,
        alignment="conflicted",
        flags=["stale_snapshot", "missing_probability_inputs"],
    )

    assert 0.0 <= score <= 1.0


def test_confidence_score_is_bounded_in_unit_interval() -> None:
    confidence = compute_candidate_confidence_score(
        link_confidence=2.0,
        comparison_confidence=-1.0,
        evidence_freshness=3.0,
        evidence_liquidity=-2.0,
        crypto_freshness=2.0,
        crypto_coverage=-1.0,
        divergence_score=3.0,
        alignment="insufficient",
        flags=["stale_evidence", "missing_probability_inputs"],
    )

    assert 0.0 <= confidence <= 1.0


def test_conflict_score_is_bounded_in_unit_interval() -> None:
    conflict = compute_candidate_conflict_score(
        divergence_score=3.0,
        alignment="conflicted",
        flags=["stale_snapshot", "missing_probability_inputs", "high_internal_dispersion"],
    )

    assert 0.0 <= conflict <= 1.0


def test_posture_thresholds_are_deterministic() -> None:
    candidate = classify_candidate_posture(
        candidate_score=0.74,
        confidence_score=0.68,
        conflict_score=0.24,
        alignment="aligned",
        comparison_confidence=0.72,
        evidence_score=0.77,
        crypto_coverage=0.81,
        has_probability_inputs=True,
        divergence_score=0.21,
    )
    watch = classify_candidate_posture(
        candidate_score=0.47,
        confidence_score=0.56,
        conflict_score=0.33,
        alignment="weakly_aligned",
        comparison_confidence=0.52,
        evidence_score=0.62,
        crypto_coverage=0.61,
        has_probability_inputs=True,
        divergence_score=0.35,
    )
    high_conflict = classify_candidate_posture(
        candidate_score=0.58,
        confidence_score=0.49,
        conflict_score=0.79,
        alignment="conflicted",
        comparison_confidence=0.61,
        evidence_score=0.71,
        crypto_coverage=0.74,
        has_probability_inputs=True,
        divergence_score=0.76,
    )
    insufficient = classify_candidate_posture(
        candidate_score=0.70,
        confidence_score=0.62,
        conflict_score=0.28,
        alignment="aligned",
        comparison_confidence=0.21,
        evidence_score=0.66,
        crypto_coverage=0.75,
        has_probability_inputs=True,
        divergence_score=0.2,
    )

    assert candidate == "candidate"
    assert watch == "watch"
    assert high_conflict == "high_conflict"
    assert insufficient == "insufficient"


def test_reason_code_derivation_is_deterministic() -> None:
    reason_codes_a = derive_candidate_reason_codes(
        alignment="aligned",
        candidate_score=0.78,
        comparison_confidence=0.72,
        conflict_score=0.2,
        divergence_score=0.14,
        evidence_liquidity=0.81,
        evidence_freshness=0.88,
        crypto_coverage=0.84,
        crypto_freshness=0.82,
        has_probability_inputs=True,
        flags=[],
    )
    reason_codes_b = derive_candidate_reason_codes(
        alignment="aligned",
        candidate_score=0.78,
        comparison_confidence=0.72,
        conflict_score=0.2,
        divergence_score=0.14,
        evidence_liquidity=0.81,
        evidence_freshness=0.88,
        crypto_coverage=0.84,
        crypto_freshness=0.82,
        has_probability_inputs=True,
        flags=[],
    )

    assert reason_codes_a == reason_codes_b == ["strong_cross_market_alignment"]
