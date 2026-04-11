"""Deterministic Polymarket-vs-crypto comparison contracts and comparator."""

from future_system.comparison.comparator import compare_theme_evidence_packets
from future_system.comparison.models import (
    ComparisonAlignment,
    ComparisonDirection,
    ComparisonError,
    EvidenceFamilySummary,
    ThemeComparisonPacket,
)
from future_system.comparison.scoring import (
    clamp_unit,
    classify_alignment,
    compute_agreement_score,
    compute_comparison_confidence_score,
    compute_crypto_strength_score,
    compute_polymarket_strength_score,
    derive_crypto_direction,
    derive_polymarket_direction,
)

__all__ = [
    "ComparisonAlignment",
    "ComparisonDirection",
    "ComparisonError",
    "EvidenceFamilySummary",
    "ThemeComparisonPacket",
    "clamp_unit",
    "classify_alignment",
    "compare_theme_evidence_packets",
    "compute_agreement_score",
    "compute_comparison_confidence_score",
    "compute_crypto_strength_score",
    "compute_polymarket_strength_score",
    "derive_crypto_direction",
    "derive_polymarket_direction",
]

