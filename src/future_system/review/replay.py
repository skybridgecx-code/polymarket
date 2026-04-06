"""Deterministic in-memory replay harness for bounded review scenarios."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from future_system.observability.audit import AuditRecord
from future_system.observability.correlation import TraceLink
from future_system.observability.events import FutureSystemEvent
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
from future_system.review.packets import FutureSystemReviewPacket, build_review_packets
from future_system.review.recommendations import (
    ReviewRecommendation,
    recommend_review_steps,
)
from future_system.review.reports import ReviewReport, render_review_report


class ReviewReplayScenario(BaseModel):
    """Fixed in-memory scenario for the bounded review harness."""

    scenario_name: str
    events: list[FutureSystemEvent]
    audit_records: list[AuditRecord]
    trace_links: list[TraceLink]
    expected_review_ready: bool
    expected_evidence_status: EvidenceStatus
    expected_deficiency_category: DeficiencyCategory


class ReviewReplayResult(BaseModel):
    """Deterministic result for one replayed review scenario."""

    scenario_name: str
    packet: FutureSystemReviewPacket
    evidence: ReviewPacketEvidence
    deficiency_summary: DeficiencySummary
    recommendations: ReviewRecommendation
    bundle: ReviewBundle
    report: ReviewReport
    review_ready: bool


def run_review_replay(scenario: ReviewReplayScenario) -> ReviewReplayResult:
    """Run one bounded scenario through the existing review pipeline."""

    packets = build_review_packets(
        events=scenario.events,
        audit_records=scenario.audit_records,
        trace_links=scenario.trace_links,
    )
    if len(packets) != 1:
        raise ValueError("review_replay_requires_single_packet")

    packet = packets[0]
    evidence = evaluate_review_packet(packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    bundle = format_review_bundle(
        packet,
        evidence,
        deficiency_summary,
        recommendations,
    )
    report = render_review_report(bundle)

    return ReviewReplayResult(
        scenario_name=scenario.scenario_name,
        packet=packet,
        evidence=evidence,
        deficiency_summary=deficiency_summary,
        recommendations=recommendations,
        bundle=bundle,
        report=report,
        review_ready=report.review_ready,
    )


def run_review_scenario_pack(
    scenarios: Sequence[ReviewReplayScenario],
) -> list[ReviewReplayResult]:
    """Run a bounded deterministic scenario pack through the replay harness."""

    return [run_review_replay(scenario) for scenario in scenarios]
