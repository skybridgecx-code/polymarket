"""Deterministic theme-linked news evidence contracts and assembler."""

from future_system.news_evidence.assembler import assemble_theme_news_evidence_packet
from future_system.news_evidence.models import (
    MatchedNewsEvidence,
    NewsEvidenceAssemblyError,
    ThemeNewsEvidencePacket,
)
from future_system.news_evidence.scoring import (
    clamp_unit,
    compute_news_coverage_score,
    compute_news_freshness_score,
    compute_news_trust_score,
)

__all__ = [
    "MatchedNewsEvidence",
    "NewsEvidenceAssemblyError",
    "ThemeNewsEvidencePacket",
    "assemble_theme_news_evidence_packet",
    "clamp_unit",
    "compute_news_coverage_score",
    "compute_news_freshness_score",
    "compute_news_trust_score",
]
