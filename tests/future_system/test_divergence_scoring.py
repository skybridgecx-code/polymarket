"""Scoring tests for deterministic divergence helpers."""

from __future__ import annotations

from future_system.divergence.scoring import (
    classify_divergence_posture,
    classify_market_disagreement_severity,
    compute_dispersion_score,
    compute_divergence_score,
    compute_quality_penalty,
)


def test_dispersion_score_is_bounded_in_unit_interval() -> None:
    low = compute_dispersion_score(distances_from_aggregate=[])
    high = compute_dispersion_score(distances_from_aggregate=[0.0, 2.0, -1.0])

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_quality_penalty_is_bounded_in_unit_interval() -> None:
    low = compute_quality_penalty(liquidity_score=2.0, freshness_score=2.0, flags=[])
    high = compute_quality_penalty(
        liquidity_score=-1.0,
        freshness_score=2.0,
        flags=[
            "stale_evidence",
            "weak_liquidity",
            "missing_implied_probability",
            "missing_probability_inputs",
            "no_aggregate_probability",
            "missing_book_data",
        ],
    )

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_divergence_score_is_bounded_in_unit_interval() -> None:
    low = compute_divergence_score(dispersion_score=-1.0, quality_penalty=2.0)
    high = compute_divergence_score(dispersion_score=2.0, quality_penalty=2.0)

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_posture_thresholds_are_deterministic_for_known_inputs() -> None:
    aligned = classify_divergence_posture(
        aggregate_yes_probability=0.55,
        usable_market_count=3,
        total_market_count=3,
        missing_probability_count=0,
        dispersion_score=0.12,
        quality_penalty=0.2,
        divergence_score=0.15,
    )
    mixed = classify_divergence_posture(
        aggregate_yes_probability=0.55,
        usable_market_count=3,
        total_market_count=3,
        missing_probability_count=0,
        dispersion_score=0.35,
        quality_penalty=0.3,
        divergence_score=0.335,
    )
    conflicted = classify_divergence_posture(
        aggregate_yes_probability=0.55,
        usable_market_count=3,
        total_market_count=3,
        missing_probability_count=0,
        dispersion_score=0.71,
        quality_penalty=0.2,
        divergence_score=0.557,
    )
    insufficient = classify_divergence_posture(
        aggregate_yes_probability=None,
        usable_market_count=3,
        total_market_count=3,
        missing_probability_count=0,
        dispersion_score=0.0,
        quality_penalty=0.2,
        divergence_score=0.06,
    )

    assert aligned == "aligned"
    assert mixed == "mixed"
    assert conflicted == "conflicted"
    assert insufficient == "insufficient"


def test_market_disagreement_severity_buckets_are_deterministic() -> None:
    assert classify_market_disagreement_severity(distance_from_aggregate=None) == "unknown"
    assert classify_market_disagreement_severity(distance_from_aggregate=0.02) == "low"
    assert classify_market_disagreement_severity(distance_from_aggregate=0.08) == "medium"
    assert classify_market_disagreement_severity(distance_from_aggregate=0.22) == "high"


def test_known_scoring_outputs_are_deterministic() -> None:
    dispersion_a = compute_dispersion_score(distances_from_aggregate=[0.03, 0.06, 0.12])
    dispersion_b = compute_dispersion_score(distances_from_aggregate=[0.03, 0.06, 0.12])
    quality_a = compute_quality_penalty(
        liquidity_score=0.8,
        freshness_score=0.9,
        flags=[],
    )
    quality_b = compute_quality_penalty(
        liquidity_score=0.8,
        freshness_score=0.9,
        flags=[],
    )
    divergence_a = compute_divergence_score(
        dispersion_score=dispersion_a,
        quality_penalty=quality_a,
    )
    divergence_b = compute_divergence_score(
        dispersion_score=dispersion_b,
        quality_penalty=quality_b,
    )

    assert dispersion_a == dispersion_b == 0.233
    assert quality_a == quality_b == 0.135
    assert divergence_a == divergence_b == 0.204

