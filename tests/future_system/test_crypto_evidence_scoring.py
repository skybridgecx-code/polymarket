"""Scoring tests for deterministic crypto evidence helpers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from future_system.crypto_evidence.scoring import (
    compute_crypto_coverage_score,
    compute_crypto_freshness_score,
    compute_crypto_liquidity_score,
)


def test_crypto_freshness_score_uses_expected_buckets() -> None:
    reference = datetime(2026, 2, 1, 12, 10, tzinfo=UTC)

    assert compute_crypto_freshness_score(
        snapshot_at=datetime(2026, 2, 1, 12, 6, tzinfo=UTC),
        reference_time=reference,
    ) == 1.0
    assert compute_crypto_freshness_score(
        snapshot_at=datetime(2026, 2, 1, 11, 45, tzinfo=UTC),
        reference_time=reference,
    ) == 0.8
    assert compute_crypto_freshness_score(
        snapshot_at=datetime(2026, 2, 1, 10, 30, tzinfo=UTC),
        reference_time=reference,
    ) == 0.5
    assert compute_crypto_freshness_score(
        snapshot_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        reference_time=reference,
    ) == 0.2


def test_crypto_liquidity_score_is_bounded() -> None:
    low = compute_crypto_liquidity_score(
        market_type="spot",
        bid_price=None,
        ask_price=None,
        volume_24h=0.0,
        open_interest=None,
    )
    high = compute_crypto_liquidity_score(
        market_type="perp",
        bid_price=10.0,
        ask_price=10.001,
        volume_24h=5_000_000.0,
        open_interest=50_000_000.0,
    )

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_crypto_coverage_score_is_bounded() -> None:
    assert compute_crypto_coverage_score(matched_count=0, linked_count=3) == 0.0
    assert compute_crypto_coverage_score(matched_count=5, linked_count=3) == 1.0
    assert compute_crypto_coverage_score(matched_count=2, linked_count=3) == 0.667


def test_crypto_scoring_outputs_are_deterministic_for_known_inputs() -> None:
    liquidity_a = compute_crypto_liquidity_score(
        market_type="perp",
        bid_price=100.0,
        ask_price=100.2,
        volume_24h=200000.0,
        open_interest=12000000.0,
    )
    liquidity_b = compute_crypto_liquidity_score(
        market_type="perp",
        bid_price=100.0,
        ask_price=100.2,
        volume_24h=200000.0,
        open_interest=12000000.0,
    )
    coverage_a = compute_crypto_coverage_score(matched_count=2, linked_count=3)
    coverage_b = compute_crypto_coverage_score(matched_count=2, linked_count=3)

    assert liquidity_a == liquidity_b == 0.982
    assert coverage_a == coverage_b == 0.667


def test_crypto_coverage_score_rejects_non_positive_linked_count() -> None:
    with pytest.raises(ValueError):
        compute_crypto_coverage_score(matched_count=1, linked_count=0)

