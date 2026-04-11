"""Ranking behavior tests for deterministic candidate signal ordering."""

from __future__ import annotations

from future_system.candidates.models import CandidateSignalPacket
from future_system.candidates.ranker import (
    build_candidate_rank_entries,
    rank_candidate_signal_packets,
)


def test_ranking_order_uses_candidate_score_first() -> None:
    ranked = rank_candidate_signal_packets(
        candidate_packets=[
            _packet(theme_id="theme_low", candidate_score=0.61),
            _packet(theme_id="theme_high", candidate_score=0.83),
        ]
    )

    assert [packet.theme_id for packet in ranked] == ["theme_high", "theme_low"]


def test_lower_conflict_wins_on_candidate_score_tie() -> None:
    ranked = rank_candidate_signal_packets(
        candidate_packets=[
            _packet(theme_id="theme_high_conflict", candidate_score=0.72, conflict_score=0.34),
            _packet(theme_id="theme_low_conflict", candidate_score=0.72, conflict_score=0.21),
        ]
    )

    assert [packet.theme_id for packet in ranked] == ["theme_low_conflict", "theme_high_conflict"]


def test_higher_confidence_wins_next_tie_break() -> None:
    ranked = rank_candidate_signal_packets(
        candidate_packets=[
            _packet(
                theme_id="theme_low_confidence",
                candidate_score=0.72,
                conflict_score=0.3,
                confidence_score=0.52,
            ),
            _packet(
                theme_id="theme_high_confidence",
                candidate_score=0.72,
                conflict_score=0.3,
                confidence_score=0.61,
            ),
        ]
    )

    assert [packet.theme_id for packet in ranked] == [
        "theme_high_confidence",
        "theme_low_confidence",
    ]


def test_theme_id_ascending_is_final_tie_break() -> None:
    ranked = rank_candidate_signal_packets(
        candidate_packets=[
            _packet(
                theme_id="theme_b",
                candidate_score=0.7,
                conflict_score=0.2,
                confidence_score=0.6,
            ),
            _packet(
                theme_id="theme_a",
                candidate_score=0.7,
                conflict_score=0.2,
                confidence_score=0.6,
            ),
        ]
    )

    assert [packet.theme_id for packet in ranked] == ["theme_a", "theme_b"]


def test_optional_insufficient_filtering_is_deterministic() -> None:
    packets = [
        _packet(theme_id="theme_candidate", posture="candidate", candidate_score=0.78),
        _packet(theme_id="theme_watch", posture="watch", candidate_score=0.52),
        _packet(theme_id="theme_insufficient", posture="insufficient", candidate_score=0.91),
    ]

    ranked = rank_candidate_signal_packets(candidate_packets=packets, exclude_insufficient=True)
    rank_entries = build_candidate_rank_entries(
        candidate_packets=packets,
        exclude_insufficient=True,
    )

    assert [packet.theme_id for packet in ranked] == ["theme_candidate", "theme_watch"]
    assert [(entry.rank, entry.signal.theme_id) for entry in rank_entries] == [
        (1, "theme_candidate"),
        (2, "theme_watch"),
    ]


def _packet(
    *,
    theme_id: str,
    posture: str = "watch",
    candidate_score: float = 0.5,
    conflict_score: float = 0.3,
    confidence_score: float = 0.5,
) -> CandidateSignalPacket:
    return CandidateSignalPacket.model_validate(
        {
            "theme_id": theme_id,
            "title": None,
            "posture": posture,
            "candidate_score": candidate_score,
            "confidence_score": confidence_score,
            "conflict_score": conflict_score,
            "alignment": "aligned",
            "primary_market_slug": None,
            "primary_symbol": None,
            "reason_codes": [],
            "flags": [],
            "explanation": f"Rank fixture for {theme_id}.",
        }
    )
