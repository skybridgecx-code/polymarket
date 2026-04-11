"""Deterministic scoring tests for future_system evidence helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from future_system.evidence.freshness import compute_freshness_score
from future_system.evidence.scoring import (
    compute_evidence_score,
    compute_liquidity_score,
    weighted_probability_average,
)


def test_freshness_score_uses_expected_buckets() -> None:
    reference = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    assert compute_freshness_score(
        snapshot_at=datetime(2026, 1, 1, 11, 56, tzinfo=UTC),
        reference_time=reference,
    ) == 1.0
    assert compute_freshness_score(
        snapshot_at=datetime(2026, 1, 1, 11, 35, tzinfo=UTC),
        reference_time=reference,
    ) == 0.8
    assert compute_freshness_score(
        snapshot_at=datetime(2026, 1, 1, 10, 30, tzinfo=UTC),
        reference_time=reference,
    ) == 0.5
    assert compute_freshness_score(
        snapshot_at=datetime(2026, 1, 1, 9, 30, tzinfo=UTC),
        reference_time=reference,
    ) == 0.2


def test_liquidity_score_is_bounded_with_extreme_inputs() -> None:
    low = compute_liquidity_score(
        spread=1.0,
        depth_near_mid=0.0,
        volume_24h=0.0,
    )
    high = compute_liquidity_score(
        spread=-4.0,
        depth_near_mid=1_000_000.0,
        volume_24h=5_000_000.0,
    )

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_evidence_score_is_bounded() -> None:
    assert 0.0 <= compute_evidence_score(liquidity_score=-2.0, freshness_score=0.5) <= 1.0
    assert 0.0 <= compute_evidence_score(liquidity_score=2.0, freshness_score=4.0) <= 1.0


def test_scoring_outputs_are_deterministic_for_known_inputs() -> None:
    liquidity_a = compute_liquidity_score(
        spread=0.04,
        depth_near_mid=1250.0,
        volume_24h=25000.0,
    )
    liquidity_b = compute_liquidity_score(
        spread=0.04,
        depth_near_mid=1250.0,
        volume_24h=25000.0,
    )
    evidence_a = compute_evidence_score(liquidity_score=liquidity_a, freshness_score=0.8)
    evidence_b = compute_evidence_score(liquidity_score=liquidity_b, freshness_score=0.8)
    weighted_a = weighted_probability_average(
        probabilities=[0.61, 0.53],
        weights=[liquidity_a, 0.4],
    )
    weighted_b = weighted_probability_average(
        probabilities=[0.61, 0.53],
        weights=[liquidity_b, 0.4],
    )

    assert liquidity_a == liquidity_b == 0.605
    assert evidence_a == evidence_b == 0.683
    assert weighted_a == weighted_b == 0.578159
