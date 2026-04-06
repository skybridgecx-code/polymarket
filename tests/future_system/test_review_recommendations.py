"""Structural and deterministic checks for review recommendation guidance."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.deficiencies import summarize_deficiencies
from future_system.review.evidence import evaluate_review_packet
from future_system.review.packets import build_review_packets
from future_system.review.recommendations import (
    ReviewRecommendation,
    recommend_review_steps,
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


def test_sufficient_summaries_produce_stable_minimal_recommendations() -> None:
    summary = _sufficient_summary()

    recommendation_a = recommend_review_steps(summary)
    recommendation_b = recommend_review_steps(summary)

    assert recommendation_a.model_dump() == recommendation_b.model_dump()
    assert recommendation_a.review_ready is True
    assert recommendation_a.manual_review_required is False
    assert recommendation_a.recommended_checks == [
        "Confirm the packet contents stay unchanged during bounded review."
    ]


def test_completeness_deficiencies_produce_missing_component_recommendations() -> None:
    packet = build_review_packets(
        events=[_event("ev-only", CorrelationId(value="corr-2"), _T1)],
        audit_records=[],
        trace_links=[],
    )[0]
    recommendation = recommend_review_steps(
        summarize_deficiencies(evaluate_review_packet(packet))
    )

    assert recommendation.review_ready is False
    assert recommendation.manual_review_required is True
    assert "missing-component inspection" in recommendation.recommendation_headline
    assert recommendation.recommended_checks == [
        "Inspect the packet for absent audit records.",
        "Inspect the packet for absent trace links.",
    ]


def test_attribution_deficiencies_produce_attribution_focused_recommendations() -> None:
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-3"), _T1)],
        audit_records=[_audit("aud-a", "corr-3", 1, _T1)],
        trace_links=[_trace("corr-3", 1, _T1)],
    )[0]
    broken = packet.model_copy(
        update={
            "events": [packet.events[0].model_copy(update={"attributed_to": ""})]
        }
    )
    recommendation = recommend_review_steps(
        summarize_deficiencies(evaluate_review_packet(broken))
    )

    assert "attribution-trail inspection" in recommendation.recommendation_headline
    assert recommendation.recommended_checks == [
        "Inspect event attribution fields for missing or blank values.",
        "Inspect audit actor, action, granted_by, and rationale fields.",
    ]
    assert "attribution trail" in recommendation.inspection_focus.lower()


def test_traceability_deficiencies_produce_trace_focused_recommendations() -> None:
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-4"), _T1)],
        audit_records=[_audit("aud-a", "corr-4", 1, _T1)],
        trace_links=[_trace("corr-4", 1, _T1)],
    )[0]
    broken = packet.model_copy(
        update={"events": [*packet.events, _event("ev-b", CorrelationId(value="wrong"), _T2)]}
    )
    recommendation = recommend_review_steps(
        summarize_deficiencies(evaluate_review_packet(broken))
    )

    assert "trace-consistency inspection" in recommendation.recommendation_headline
    assert recommendation.recommended_checks == [
        "Inspect correlation_id consistency across packet records.",
        "Inspect trace sequence continuity and audit-trace membership.",
    ]
    assert "trace consistency" in recommendation.inspection_focus.lower()


def test_mixed_deficiencies_produce_deterministic_combined_recommendations() -> None:
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-5"), _T1)],
        audit_records=[_audit("aud-a", "corr-5", 1, _T1)],
        trace_links=[_trace("corr-5", 1, _T1)],
    )[0]
    broken = packet.model_copy(
        update={
            "events": [
                packet.events[0].model_copy(
                    update={
                        "attributed_to": "",
                        "correlation_id": CorrelationId(value="wrong"),
                    }
                )
            ]
        }
    )
    recommendation = recommend_review_steps(
        summarize_deficiencies(evaluate_review_packet(broken))
    )

    assert recommendation.recommended_checks == [
        "Inspect event attribution fields for missing or blank values.",
        "Inspect audit actor, action, granted_by, and rationale fields.",
        "Inspect correlation_id consistency across packet records.",
        "Inspect trace sequence continuity and audit-trace membership.",
    ]
    assert recommendation.manual_review_required is True


def test_recommendation_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "recommendations.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_recommendation_model_has_no_forbidden_fields() -> None:
    for field_name in ReviewRecommendation.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ReviewRecommendation"
        )


def _sufficient_summary():
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-1"), _T1)],
        audit_records=[_audit("aud-a", "corr-1", 1, _T1)],
        trace_links=[_trace("corr-1", 1, _T1), _trace("corr-1", 2, _T2)],
    )[0]
    return summarize_deficiencies(evaluate_review_packet(packet))


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
        description="Review recommendation test event.",
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
        action="inspect-review-guidance",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic recommendation test audit record.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
