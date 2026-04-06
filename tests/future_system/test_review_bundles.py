"""Structural and deterministic checks for review bundle formatting."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from future_system.observability.audit import AuditRecord, DecisionKind
from future_system.observability.correlation import CorrelationId, RecordScope, TraceLink
from future_system.observability.events import EventKind, FutureSystemEvent
from future_system.review.bundles import ReviewBundle, format_review_bundle
from future_system.review.deficiencies import summarize_deficiencies
from future_system.review.evidence import evaluate_review_packet
from future_system.review.packets import build_review_packets
from future_system.review.recommendations import recommend_review_steps

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


def test_complete_review_chain_produces_deterministic_bundle_output() -> None:
    packet, evidence, deficiency_summary, recommendations = _review_chain("corr-1")

    bundle_a = format_review_bundle(packet, evidence, deficiency_summary, recommendations)
    bundle_b = format_review_bundle(packet, evidence, deficiency_summary, recommendations)

    assert bundle_a.model_dump() == bundle_b.model_dump()
    assert bundle_a.review_ready is True
    assert bundle_a.manual_review_required is False
    assert bundle_a.bundle_headline == (
        f"Packet {packet.packet_id} is bundled for bounded review."
    )
    assert bundle_a.final_inspection_focus == "Minimal bounded review confirmation only."


def test_incomplete_review_chain_bundles_with_explicit_review_limits() -> None:
    packet = build_review_packets(
        events=[_event("ev-only", CorrelationId(value="corr-2"), _T1)],
        audit_records=[],
        trace_links=[],
    )[0]
    evidence = evaluate_review_packet(packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)

    bundle = format_review_bundle(packet, evidence, deficiency_summary, recommendations)

    assert bundle.review_ready is False
    assert bundle.manual_review_required is True
    assert bundle.bundle_headline == (
        f"Packet {packet.packet_id} is bundled with explicit review limits; "
        "missing components prevent bounded review."
    )
    assert bundle.final_inspection_focus == (
        "Inspect absent packet components before any further review."
    )
    assert bundle.deficiency_summary.missing_components == packet.missing_components


def test_bundle_headline_is_deterministic_for_insufficient_packets() -> None:
    packet, evidence, deficiency_summary, recommendations = _attribution_broken_chain()

    bundle_a = format_review_bundle(packet, evidence, deficiency_summary, recommendations)
    bundle_b = format_review_bundle(packet, evidence, deficiency_summary, recommendations)

    assert bundle_a.bundle_headline == bundle_b.bundle_headline
    assert bundle_a.bundle_headline == (
        f"Packet {packet.packet_id} is bundled with explicit review limits; "
        "manual inspection is required before bounded review."
    )


def test_final_inspection_focus_is_deterministic_for_mixed_deficiencies() -> None:
    packet, evidence, deficiency_summary, recommendations = _mixed_broken_chain()

    bundle_a = format_review_bundle(packet, evidence, deficiency_summary, recommendations)
    bundle_b = format_review_bundle(packet, evidence, deficiency_summary, recommendations)

    assert bundle_a.final_inspection_focus == bundle_b.final_inspection_focus
    assert bundle_a.final_inspection_focus == (
        "Inspect attribution trail first, then inspect trace consistency."
    )


def test_bundle_output_is_pure_in_memory_only() -> None:
    for filename in ("__init__.py", "bundles.py"):
        source = (_REVIEW_SRC / filename).read_text()
        assert "polymarket_arb" not in source
        for term in _FORBIDDEN_IO_TERMS:
            assert term not in source, f"Forbidden I/O token {term!r} found in {filename}"
        source_words = set(re.findall(r"[a-z]+", source.lower()))
        matched = source_words & _FORBIDDEN_SOURCE_WORDS
        assert not matched, (
            f"Forbidden semantic word(s) {matched} found in {filename}"
        )


def test_bundle_model_has_no_forbidden_fields() -> None:
    for field_name in ReviewBundle.model_fields:
        parts = set(field_name.lower().split("_"))
        matched = parts & _FORBIDDEN_FIELD_TERMS
        assert not matched, (
            f"Forbidden term(s) {matched} found in field "
            f"{field_name!r} of ReviewBundle"
        )


def _review_chain(correlation_value: str):
    packet = build_review_packets(
        events=[_event("ev-a", CorrelationId(value=correlation_value), _T1)],
        audit_records=[_audit("aud-a", correlation_value, 1, _T1)],
        trace_links=[_trace(correlation_value, 1, _T1), _trace(correlation_value, 2, _T2)],
    )[0]
    evidence = evaluate_review_packet(packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return packet, evidence, deficiency_summary, recommendations


def _attribution_broken_chain():
    packet, _, _, _ = _review_chain("corr-3")
    broken_packet = packet.model_copy(
        update={"events": [packet.events[0].model_copy(update={"attributed_to": ""})]}
    )
    evidence = evaluate_review_packet(broken_packet)
    deficiency_summary = summarize_deficiencies(evidence)
    recommendations = recommend_review_steps(deficiency_summary)
    return broken_packet, evidence, deficiency_summary, recommendations


def _mixed_broken_chain():
    packet, _, _, _ = _review_chain("corr-4")
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
    return broken_packet, evidence, deficiency_summary, recommendations


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
        description="Review bundle test event.",
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
        action="assemble-review-bundle",
        granted_by="governance-role",
        decided_at=decided_at,
        trace=_trace(correlation_id, sequence, decided_at),
        decision_kind=DecisionKind.APPROVAL,
        rationale="Deterministic review bundle test audit record.",
    )


def _trace(correlation_id: str, sequence: int, created_at: datetime) -> TraceLink:
    return TraceLink(
        correlation_id=correlation_id,
        record_scope=RecordScope.GOVERNANCE,
        sequence=sequence,
        created_at=created_at,
    )
