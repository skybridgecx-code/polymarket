"""Review-packet layer for future-system records.

Builds deterministic in-memory packets from future-system event, audit,
and trace records.
"""

from future_system.review.bundles import ReviewBundle, format_review_bundle
from future_system.review.deficiencies import (
    DeficiencyCategory,
    DeficiencySummary,
    summarize_deficiencies,
)
from future_system.review.evidence import (
    EvidenceStatus,
    ReviewPacketEvidence,
    evaluate_review_packet,
)
from future_system.review.packets import (
    FutureSystemReviewPacket,
    PacketCompletenessStatus,
    PacketMissingComponent,
    ReviewPacketScope,
    build_review_packets,
)
from future_system.review.recommendations import (
    ReviewRecommendation,
    recommend_review_steps,
)
from future_system.review.replay import (
    ReviewReplayResult,
    ReviewReplayScenario,
    run_review_replay,
)
from future_system.review.reports import ReviewReport, render_review_report

__all__ = [
    "DeficiencyCategory",
    "DeficiencySummary",
    "EvidenceStatus",
    "FutureSystemReviewPacket",
    "PacketCompletenessStatus",
    "PacketMissingComponent",
    "ReviewBundle",
    "ReviewRecommendation",
    "ReviewReplayResult",
    "ReviewReplayScenario",
    "ReviewReport",
    "ReviewPacketEvidence",
    "ReviewPacketScope",
    "build_review_packets",
    "evaluate_review_packet",
    "format_review_bundle",
    "recommend_review_steps",
    "run_review_replay",
    "render_review_report",
    "summarize_deficiencies",
]
