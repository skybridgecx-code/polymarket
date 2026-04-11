"""Deterministic ranking helpers for candidate signal packets."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.candidates.models import CandidateRankEntry, CandidateSignalPacket


def rank_candidate_signal_packets(
    *,
    candidate_packets: Sequence[CandidateSignalPacket],
    exclude_insufficient: bool = False,
) -> list[CandidateSignalPacket]:
    """Rank candidate signals deterministically by score, conflict, confidence, then theme id."""

    packets = list(candidate_packets)
    if exclude_insufficient:
        packets = [packet for packet in packets if packet.posture != "insufficient"]

    return sorted(
        packets,
        key=lambda packet: (
            -packet.candidate_score,
            packet.conflict_score,
            -packet.confidence_score,
            packet.theme_id,
        ),
    )


def build_candidate_rank_entries(
    *,
    candidate_packets: Sequence[CandidateSignalPacket],
    exclude_insufficient: bool = False,
) -> list[CandidateRankEntry]:
    """Build deterministic rank entries from ranked candidate signal packets."""

    ranked_packets = rank_candidate_signal_packets(
        candidate_packets=candidate_packets,
        exclude_insufficient=exclude_insufficient,
    )
    return [
        CandidateRankEntry(rank=index, signal=packet)
        for index, packet in enumerate(ranked_packets, start=1)
    ]
