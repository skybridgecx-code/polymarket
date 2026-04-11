"""Deterministic candidate signal contracts, scoring, builder, and ranking."""

from future_system.candidates.builder import build_candidate_signal_packet
from future_system.candidates.models import (
    CandidateBuildError,
    CandidatePosture,
    CandidateRankEntry,
    CandidateReasonCode,
    CandidateSignalPacket,
)
from future_system.candidates.ranker import (
    build_candidate_rank_entries,
    rank_candidate_signal_packets,
)
from future_system.candidates.scoring import (
    clamp_unit,
    classify_candidate_posture,
    compute_candidate_confidence_score,
    compute_candidate_conflict_score,
    compute_candidate_score,
    derive_candidate_reason_codes,
)

__all__ = [
    "CandidateBuildError",
    "CandidatePosture",
    "CandidateRankEntry",
    "CandidateReasonCode",
    "CandidateSignalPacket",
    "build_candidate_rank_entries",
    "build_candidate_signal_packet",
    "clamp_unit",
    "classify_candidate_posture",
    "compute_candidate_confidence_score",
    "compute_candidate_conflict_score",
    "compute_candidate_score",
    "derive_candidate_reason_codes",
    "rank_candidate_signal_packets",
]
