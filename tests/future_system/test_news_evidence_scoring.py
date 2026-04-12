"""Scoring tests for deterministic theme-linked news evidence helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from future_system.news_evidence.scoring import (
    compute_news_coverage_score,
    compute_news_freshness_score,
    compute_news_trust_score,
)


def test_news_freshness_score_uses_expected_buckets() -> None:
    reference = datetime(2026, 4, 11, 12, 0, tzinfo=UTC)

    assert compute_news_freshness_score(
        published_at=datetime(2026, 4, 11, 10, 0, tzinfo=UTC),
        reference_time=reference,
    ) == 1.0
    assert compute_news_freshness_score(
        published_at=datetime(2026, 4, 11, 6, 0, tzinfo=UTC),
        reference_time=reference,
    ) == 0.8
    assert compute_news_freshness_score(
        published_at=datetime(2026, 4, 10, 14, 0, tzinfo=UTC),
        reference_time=reference,
    ) == 0.6
    assert compute_news_freshness_score(
        published_at=datetime(2026, 4, 9, 12, 0, tzinfo=UTC),
        reference_time=reference,
    ) == 0.35
    assert compute_news_freshness_score(
        published_at=datetime(2026, 4, 7, 11, 59, tzinfo=UTC),
        reference_time=reference,
    ) == 0.15


def test_news_trust_score_is_bounded_in_unit_interval() -> None:
    trust_score = compute_news_trust_score(trust_scores=[-1.0, 2.0, 0.4])

    assert 0.0 <= trust_score <= 1.0


def test_news_coverage_score_is_bounded_in_unit_interval() -> None:
    coverage_zero = compute_news_coverage_score(
        linked_entities=["sec", "federal reserve"],
        observed_linked_entities=[],
    )
    coverage_full = compute_news_coverage_score(
        linked_entities=["sec", "federal reserve"],
        observed_linked_entities=["sec", "federal reserve", "sec", "other"],
    )

    assert 0.0 <= coverage_zero <= 1.0
    assert 0.0 <= coverage_full <= 1.0


def test_news_scoring_outputs_are_deterministic_for_known_inputs() -> None:
    trust_a = compute_news_trust_score(trust_scores=[0.92, 0.84, 0.63])
    trust_b = compute_news_trust_score(trust_scores=[0.92, 0.84, 0.63])
    coverage_a = compute_news_coverage_score(
        linked_entities=["sec", "federal reserve", "bank of japan"],
        observed_linked_entities=["sec", "federal reserve"],
    )
    coverage_b = compute_news_coverage_score(
        linked_entities=["sec", "federal reserve", "bank of japan"],
        observed_linked_entities=["sec", "federal reserve"],
    )

    assert trust_a == trust_b == 0.797
    assert coverage_a == coverage_b == 0.667
