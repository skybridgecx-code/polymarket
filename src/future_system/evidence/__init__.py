"""Canonical evidence contracts and deterministic assembly utilities."""

from future_system.evidence.assembler import assemble_theme_evidence_packet
from future_system.evidence.freshness import compute_freshness_score, is_stale_snapshot
from future_system.evidence.models import (
    EvidenceAssemblyError,
    NormalizedPolymarketMarketState,
    PolymarketMarketEvidence,
    ThemeEvidencePacket,
)
from future_system.evidence.scoring import (
    clamp_unit,
    compute_evidence_score,
    compute_liquidity_score,
    weighted_probability_average,
)

__all__ = [
    "EvidenceAssemblyError",
    "NormalizedPolymarketMarketState",
    "PolymarketMarketEvidence",
    "ThemeEvidencePacket",
    "assemble_theme_evidence_packet",
    "compute_evidence_score",
    "compute_freshness_score",
    "compute_liquidity_score",
    "is_stale_snapshot",
    "clamp_unit",
    "weighted_probability_average",
]

