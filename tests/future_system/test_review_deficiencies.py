"""Structural and deterministic checks for review-packet deficiency summarizer."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.deficiencies import (
    DeficiencyCategory,
    DeficiencySummary,
    summarize_deficiencies,
)
from future_system.review.evidence import evaluate_review_packet
from future_system.review.packets import build_review_packets

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
    {"venue", "auth", "credential", "signing", "position", "submit", "live"}
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
        description="Deficiency summarizer test event.",
        attributed_to=attributed_to,
    )


def _audit(
    record_id: str,
    correlation_id: str,
    sequence: int,
    decided_at: datetime,
    actor: str = "review-actor",
    action: str = "assess-review-readiness",
    granted_by: str = "governance-role",
    rationale: str = "Deficiency summarizer test audit record.",
) -> AuditRecord:
    return AuditRecord(
        record_id=record_id,
        actor=actor,
        action=action,
        granted_by=granted_by,
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale=rationale,
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )


def _sufficient_evidence():  # type: ignore[return]
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-1"), _T1)],
        audit_records=[_audit("aud-a", "corr-1", 1, _T1)],
        trace_links=[_trace("corr-1", 1, _T1), _trace("corr-1", 2, _T2)],
    )[0]
    return evaluate_review_packet(packet)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sufficient_evidence_produces_stable_summary() -> None:
    """Summarizing the same sufficient evidence twice yields identical output."""
    evidence = _sufficient_evidence()

    summary_a = summarize_deficiencies(evidence)
    summary_b = summarize_deficiencies(evidence)

    assert summary_a.model_dump() == summary_b.model_dump()
    assert summary_a.review_ready is True
    assert summary_a.deficiency_category is DeficiencyCategory.NONE
    assert summary_a.evidence_status == evidence.evidence_status
    assert summary_a.packet_id == evidence.packet_id


def test_sufficient_evidence_produces_no_deficiency_findings() -> None:
    evidence = _sufficient_evidence()
    summary = summarize_deficiencies(evidence)

    assert summary.deficiency_category is DeficiencyCategory.NONE
    assert summary.missing_components == []
    assert "No further inspection required" in summary.inspection_focus
    assert "no deficiencies" in summary.headline
    assert all("satisfied" in f or "complete" in f.lower() for f in summary.findings)


def test_incomplete_packet_produces_completeness_findings() -> None:
    packet = build_review_packets(
        events=[_event("ev-only", CorrelationId(value="corr-2"), _T1)],
        audit_records=[],
        trace_links=[],
    )[0]
    evidence = evaluate_review_packet(packet)
    summary = summarize_deficiencies(evidence)

    assert summary.review_ready is False
    assert summary.deficiency_category is DeficiencyCategory.COMPLETENESS
    assert summary.missing_components == evidence.missing_components
    assert "missing required components" in summary.headline
    assert any("absent" in f for f in summary.findings)
    assert "missing" in summary.inspection_focus.lower()


def test_attribution_failure_produces_attribution_focused_findings() -> None:
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-3"), _T1)],
        audit_records=[_audit("aud-a", "corr-3", 1, _T1)],
        trace_links=[_trace("corr-3", 1, _T1)],
    )[0]
    # Break attribution by blanking the attributed_to field on the event
    broken = packet.model_copy(
        update={
            "events": [packet.events[0].model_copy(update={"attributed_to": ""})]
        }
    )
    evidence = evaluate_review_packet(broken)
    summary = summarize_deficiencies(evidence)

    assert summary.review_ready is False
    assert summary.deficiency_category is DeficiencyCategory.ATTRIBUTION
    assert "attribution boundary failed" in summary.headline
    assert any("attribution" in f.lower() for f in summary.findings)
    assert "actor" in summary.inspection_focus or "attributed_to" in summary.inspection_focus


def test_traceability_failure_produces_traceability_focused_findings() -> None:
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-4"), _T1)],
        audit_records=[_audit("aud-a", "corr-4", 1, _T1)],
        trace_links=[_trace("corr-4", 1, _T1)],
    )[0]
    # Break traceability: inject an event with a mismatched correlation_id
    mismatched_event = _event("ev-b", CorrelationId(value="wrong-corr"), _T2)
    broken = packet.model_copy(
        update={"events": [*packet.events, mismatched_event]}
    )
    evidence = evaluate_review_packet(broken)
    summary = summarize_deficiencies(evidence)

    assert summary.review_ready is False
    assert summary.deficiency_category is DeficiencyCategory.TRACEABILITY
    assert "traceability boundary failed" in summary.headline
    assert any("traceability" in f.lower() for f in summary.findings)
    assert "correlation" in summary.inspection_focus.lower()


def test_mixed_deficiency_produces_mixed_category() -> None:
    # Complete packet (all components present) but with both attribution failure
    # (blank attributed_to on event) and traceability failure (mismatched
    # correlation_id on one event). Both boundaries fail independently → MIXED.
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-5"), _T1)],
        audit_records=[_audit("aud-a", "corr-5", 1, _T1)],
        trace_links=[_trace("corr-5", 1, _T1)],
    )[0]
    # Blank attributed_to (attribution failure) AND inject a mismatched correlation
    # on one event (traceability failure)
    broken = packet.model_copy(
        update={
            "events": [
                packet.events[0].model_copy(
                    update={
                        "attributed_to": "",
                        "correlation_id": CorrelationId(value="wrong-corr"),
                    }
                )
            ]
        }
    )
    evidence = evaluate_review_packet(broken)
    summary = summarize_deficiencies(evidence)

    assert summary.review_ready is False
    assert summary.deficiency_category is DeficiencyCategory.MIXED
    assert "multiple deficiency boundaries failed" in summary.headline


def test_summarizer_output_is_pure_in_memory_only() -> None:
    """deficiencies.py must contain no I/O or baseline imports."""
    source = (_REVIEW_SRC / "deficiencies.py").read_text()
    assert "polymarket_arb" not in source, "Cross-import into frozen baseline detected"
    for term in _FORBIDDEN_IO_TERMS:
        assert term not in source, f"Forbidden I/O token {term!r} found in deficiencies.py"
    source_words = set(re.findall(r"[a-z]+", source.lower()))
    matched = source_words & _FORBIDDEN_SOURCE_WORDS
    assert not matched, f"Forbidden semantic word(s) {matched} found in deficiencies.py"


def test_deficiency_summary_model_has_no_forbidden_fields() -> None:
    for field_name in DeficiencySummary.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of DeficiencySummary"
        )


def test_missing_components_carried_forward_clearly() -> None:
    packet = build_review_packets(
        events=[],
        audit_records=[_audit("aud-a", "corr-6", 1, _T1)],
        trace_links=[],
    )[0]
    evidence = evaluate_review_packet(packet)
    summary = summarize_deficiencies(evidence)

    assert summary.missing_components == evidence.missing_components
    assert summary.review_ready is False
