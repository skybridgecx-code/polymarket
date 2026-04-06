"""Structural and deterministic checks for review report rendering."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.bundles import format_review_bundle
from future_system.review.deficiencies import summarize_deficiencies
from future_system.review.evidence import evaluate_review_packet
from future_system.review.packets import build_review_packets
from future_system.review.recommendations import recommend_review_steps
from future_system.review.reports import ReviewReport, render_review_report

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


def test_complete_bundles_produce_deterministic_report_output() -> None:
    bundle = _review_bundle("corr-1")

    report_a = render_review_report(bundle)
    report_b = render_review_report(bundle)

    assert report_a.model_dump() == report_b.model_dump()
    assert report_a.review_ready is True
    assert report_a.manual_review_required is False
    assert report_a.report_headline == (
        f"Packet {bundle.packet_id} is ready for bounded review."
    )
    assert report_a.readiness_summary == (
        "Bounded review may proceed; completeness, attribution, and "
        "traceability checks are satisfied."
    )


def test_incomplete_bundles_render_with_explicit_review_limits() -> None:
    packet = build_review_packets(
        events=[_event("ev-only", CorrelationId(value="corr-2"), _T1)],
        audit_records=[],
        trace_links=[],
    )[0]
    evidence = evaluate_review_packet(packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    bundle = format_review_bundle(packet, evidence, deficiency_summary, recommendations)

    report = render_review_report(bundle)

    assert report.review_ready is False
    assert report.manual_review_required is True
    assert report.missing_components == packet.missing_components
    assert report.report_headline == (
        f"Packet {bundle.packet_id} is not ready for bounded review; "
        "explicit review limits apply."
    )
    assert report.readiness_summary == (
        "Bounded review must not proceed; required packet components are "
        "missing: audit_records, ordered_trace."
    )


def test_report_headline_is_deterministic_for_insufficient_bundles() -> None:
    bundle = _attribution_broken_bundle()

    report_a = render_review_report(bundle)
    report_b = render_review_report(bundle)

    assert report_a.report_headline == report_b.report_headline
    assert report_a.report_headline == (
        f"Packet {bundle.packet_id} is not ready for bounded review; "
        "manual inspection is required."
    )


def test_readiness_summary_is_deterministic_for_traceability_gaps() -> None:
    bundle = _traceability_broken_bundle()

    report_a = render_review_report(bundle)
    report_b = render_review_report(bundle)

    assert report_a.readiness_summary == report_b.readiness_summary
    assert report_a.readiness_summary == (
        "Bounded review must not proceed; traceability boundaries remain "
        "incomplete."
    )


def test_final_inspection_focus_is_preserved_deterministically() -> None:
    bundle = _mixed_broken_bundle()

    report_a = render_review_report(bundle)
    report_b = render_review_report(bundle)

    assert report_a.final_inspection_focus == report_b.final_inspection_focus
    assert report_a.final_inspection_focus == (
        "Inspect attribution trail first, then inspect trace consistency."
    )
    assert report_a.recommended_checks == [
        "Inspect event attribution fields for missing or blank values.",
        "Inspect audit actor, action, granted_by, and rationale fields.",
        "Inspect correlation_id consistency across packet records.",
        "Inspect trace sequence continuity and audit-trace membership.",
    ]


def test_report_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "reports.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_report_model_has_no_forbidden_fields() -> None:
    for field_name in ReviewReport.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ReviewReport"
        )


def _review_bundle(correlation_value: str):
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value=correlation_value), _T1)],
        audit_records=[_audit("aud-a", correlation_value, 1, _T1)],
        trace_links=[_trace(correlation_value, 1, _T1), _trace(correlation_value, 2, _T2)],
    )[0]
    evidence = evaluate_review_packet(packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return format_review_bundle(packet, evidence, deficiency_summary, recommendations)


def _attribution_broken_bundle():
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-3"), _T1)],
        audit_records=[_audit("aud-a", "corr-3", 1, _T1)],
        trace_links=[_trace("corr-3", 1, _T1)],
    )[0]
    broken_packet = packet.model_copy(
        update={"events": [packet.events[0].model_copy(update={"attributed_to": ""})]}
    )
    evidence = evaluate_review_packet(broken_packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return format_review_bundle(
        broken_packet,
        evidence,
        deficiency_summary,
        recommendations,
    )


def _traceability_broken_bundle():
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-4"), _T1)],
        audit_records=[_audit("aud-a", "corr-4", 1, _T1)],
        trace_links=[_trace("corr-4", 1, _T1)],
    )[0]
    broken_packet = packet.model_copy(
        update={"events": [*packet.events, _event("ev-b", CorrelationId(value="wrong"), _T2)]}
    )
    evidence = evaluate_review_packet(broken_packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return format_review_bundle(
        broken_packet,
        evidence,
        deficiency_summary,
        recommendations,
    )


def _mixed_broken_bundle():
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value="corr-5"), _T1)],
        audit_records=[_audit("aud-a", "corr-5", 1, _T1)],
        trace_links=[_trace("corr-5", 1, _T1)],
    )[0]
    broken_packet = packet.model_copy(
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
    evidence = evaluate_review_packet(broken_packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return format_review_bundle(
        broken_packet,
        evidence,
        deficiency_summary,
        recommendations,
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
        description="Review report test event.",
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
        action="render-review-report",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic review report test audit record.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
