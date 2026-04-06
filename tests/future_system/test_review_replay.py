"""Structural and deterministic checks for review replay scenarios."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.deficiencies import DeficiencyCategory
from future_system.review.evidence import EvidenceStatus
from future_system.review.replay import (
    ReviewReplayResult,
    ReviewReplayScenario,
    run_review_replay,
)

_T1 = datetime(2025, 1, 1, 0, 1, 0)
_T2 = datetime(2025, 1, 1, 0, 2, 0)

_REVIEW_SRC = (
    Path(__file__).resolve().parent.parent.parent / "src" / "future_system" / "review"
)
_FORBIDDEN_IO_TERMS = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "socket",
    "sqlite",
    "psycopg",
    "open(",
    "write_text(",
    "write_bytes(",
)
_FORBIDDEN_SOURCE_WORDS = frozenset(
    {"venue", "auth", "credential", "signing", "position", "submit", "live", "order"}
)
_FORBIDDEN_FIELD_TERMS = frozenset(
    {
        "venue",
        "auth",
        "credential",
        "sign",
        "position",
        "submit",
        "private",
        "order",
        "live",
    }
)


def test_complete_scenario_produces_deterministic_end_to_end_output() -> None:
    scenario = _complete_scenario()

    replay_a = run_review_replay(scenario)
    replay_b = run_review_replay(scenario)

    assert replay_a.model_dump() == replay_b.model_dump()
    assert replay_a.review_ready is scenario.expected_review_ready
    assert replay_a.evidence.evidence_status is scenario.expected_evidence_status
    assert (
        replay_a.deficiency_summary.deficiency_category
        is scenario.expected_deficiency_category
    )
    assert replay_a.report.report_headline == (
        f"Packet {replay_a.packet.packet_id} is ready for bounded review."
    )


def test_incomplete_scenario_produces_deterministic_incomplete_output() -> None:
    scenario = _incomplete_scenario()

    replay = run_review_replay(scenario)

    assert replay.review_ready is scenario.expected_review_ready
    assert replay.evidence.evidence_status is scenario.expected_evidence_status
    assert (
        replay.deficiency_summary.deficiency_category
        is scenario.expected_deficiency_category
    )
    assert replay.packet.missing_components == replay.report.missing_components
    assert replay.report.readiness_summary == (
        "Bounded review must not proceed; required packet components are "
        "missing: audit_records, trace_links."
    ).replace("trace_links", "ordered_trace")


def test_attribution_deficient_scenario_produces_expected_shape() -> None:
    scenario = _attribution_scenario()

    replay = run_review_replay(scenario)

    assert replay.review_ready is scenario.expected_review_ready
    assert replay.evidence.evidence_status is scenario.expected_evidence_status
    assert (
        replay.deficiency_summary.deficiency_category
        is scenario.expected_deficiency_category
    )
    assert replay.evidence.attribution_complete is False
    assert replay.evidence.traceability_complete is True
    assert "attribution" in replay.report.readiness_summary.lower()


def test_traceability_deficient_scenario_produces_expected_shape() -> None:
    scenario = _traceability_scenario()

    replay = run_review_replay(scenario)

    assert replay.review_ready is scenario.expected_review_ready
    assert replay.evidence.evidence_status is scenario.expected_evidence_status
    assert (
        replay.deficiency_summary.deficiency_category
        is scenario.expected_deficiency_category
    )
    assert replay.evidence.attribution_complete is True
    assert replay.evidence.traceability_complete is False
    assert "traceability" in replay.report.readiness_summary.lower()


def test_replay_results_are_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "replay.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_replay_models_have_no_forbidden_fields() -> None:
    for model in (ReviewReplayScenario, ReviewReplayResult):
        for field_name in model.model_fields:
            parts = set(field_name.lower().split("_"))
            matched = parts & _FORBIDDEN_FIELD_TERMS
            assert not matched, (
                f"Forbidden term(s) {matched} found in field "
                f"{field_name!r} of {model.__name__}"
            )


def _complete_scenario() -> ReviewReplayScenario:
    return ReviewReplayScenario(
        scenario_name="complete",
        events=[_event("ev-a", CorrelationId(value="corr-1"), _T1)],
        audit_records=[_audit("aud-a", "corr-1", 1, _T1)],
        trace_links=[_trace("corr-1", 1, _T1), _trace("corr-1", 2, _T2)],
        expected_review_ready=True,
        expected_evidence_status=EvidenceStatus.SUFFICIENT,
        expected_deficiency_category=DeficiencyCategory.NONE,
    )


def _incomplete_scenario() -> ReviewReplayScenario:
    return ReviewReplayScenario(
        scenario_name="incomplete",
        events=[_event("ev-only", CorrelationId(value="corr-2"), _T1)],
        audit_records=[],
        trace_links=[],
        expected_review_ready=False,
        expected_evidence_status=EvidenceStatus.INCOMPLETE,
        expected_deficiency_category=DeficiencyCategory.COMPLETENESS,
    )


def _attribution_scenario() -> ReviewReplayScenario:
    return ReviewReplayScenario(
        scenario_name="attribution-deficient",
        events=[
            _event("ev-a", CorrelationId(value="corr-3"), _T1, attributed_to="")
        ],
        audit_records=[_audit("aud-a", "corr-3", 1, _T1)],
        trace_links=[_trace("corr-3", 1, _T1)],
        expected_review_ready=False,
        expected_evidence_status=EvidenceStatus.INSUFFICIENT,
        expected_deficiency_category=DeficiencyCategory.ATTRIBUTION,
    )


def _traceability_scenario() -> ReviewReplayScenario:
    return ReviewReplayScenario(
        scenario_name="traceability-deficient",
        events=[_event("ev-a", CorrelationId(value="corr-4"), _T1)],
        audit_records=[_audit("aud-a", "corr-4", 2, _T2)],
        trace_links=[_trace("corr-4", 1, _T1)],
        expected_review_ready=False,
        expected_evidence_status=EvidenceStatus.INSUFFICIENT,
        expected_deficiency_category=DeficiencyCategory.TRACEABILITY,
    )


def _event(
    event_id: str,
    correlation_id: CorrelationId,
    occurred_at: datetime,
    attributed_to: str = "review-actor",
) -> FutureSystemEvent:
    return FutureSystemEvent(
        event_id=event_id,
        correlation_id=correlation_id,
        event_kind=EventKind.APPROVAL_GRANTED,
        record_scope=RecordScope.GOVERNANCE,
        occurred_at=occurred_at,
        description="Review replay test event.",
        attributed_to=attributed_to,
    )


def _audit(
    record_id: str,
    correlation_id: str,
    sequence: int,
    decided_at: datetime,
) -> AuditRecord:
    return AuditRecord(
        record_id=record_id,
        actor="review-actor",
        action="replay-review-chain",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic review replay test audit record.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
