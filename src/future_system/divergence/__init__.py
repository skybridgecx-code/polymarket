"""Deterministic divergence contracts and detector for canonical evidence packets."""

from future_system.divergence.detector import detect_theme_divergence
from future_system.divergence.models import (
    DivergenceDetectionError,
    DivergencePosture,
    MarketDisagreement,
    MarketDisagreementSeverity,
    ThemeDivergencePacket,
)
from future_system.divergence.scoring import (
    clamp_unit,
    classify_divergence_posture,
    classify_market_disagreement_severity,
    compute_dispersion_score,
    compute_divergence_score,
    compute_quality_penalty,
)

__all__ = [
    "DivergenceDetectionError",
    "DivergencePosture",
    "MarketDisagreement",
    "MarketDisagreementSeverity",
    "ThemeDivergencePacket",
    "classify_divergence_posture",
    "classify_market_disagreement_severity",
    "clamp_unit",
    "compute_dispersion_score",
    "compute_divergence_score",
    "compute_quality_penalty",
    "detect_theme_divergence",
]

