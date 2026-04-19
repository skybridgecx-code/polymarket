from __future__ import annotations

from pathlib import Path

PRODUCER_CONTRACT_DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "PHASE_37I_LOCAL_TRANSPORT_WORKFLOW_CONTRACT.md"
)
CONSUMER_CONTRACT_DOC = Path(
    "/Users/muhammadaatif/cryp/docs/PHASE_37J_LOCAL_TRANSPORT_CONSUMER_WORKFLOW_CONTRACT.md"
)

# Keep this anchor set small and explainable. These are the key contract strings
# called out by Phase 37K as cross-repo drift-sensitive surfaces.
PARITY_ANCHORS = (
    "TRANSPORT_ROOT=<absolute/local/path>",
    "<TRANSPORT_ROOT>/inbound/<correlation_id>/<attempt_id>/handoff_request.json",
    "<TRANSPORT_ROOT>/pickup/<correlation_id>/<attempt_id>/cryp_pickup_receipt.json",
    "<TRANSPORT_ROOT>/responses/<correlation_id>/<attempt_id>/<correlation_id>.execution_boundary_ack.json",
    "<TRANSPORT_ROOT>/responses/<correlation_id>/<attempt_id>/<correlation_id>.execution_boundary_reject.json",
    '<run_id>:<updated_at_epoch_ns>:<operator_decision>',
    "execution_boundary_intake_ack",
    "execution_boundary_intake_reject",
    "accepted_for_local_execution_review",
    "rejected_for_local_execution_review",
)

PICKUP_RECEIPT_REQUIRED_FIELD_ANCHORS = (
    '`contract_version` (`"37A.v1"`)',
    '`producer_system` (`"polymarket-arb"`)',
    '`consumer_system` (`"cryp"`)',
    "`correlation_id`",
    "`idempotency_key`",
    '`pickup_status` (`"picked_up_for_local_execution_review"`)',
    "`picked_up_at_epoch_ns`",
    "`pickup_operator`",
    "`source_handoff_request_path`",
)

IDEMPOTENCY_RULE_SECTION_ANCHORS = (
    "<run_id>:<updated_at_epoch_ns>:<operator_decision>",
    "updated_at_epoch_ns",
    "attempt_id",
    "duplicate",
)

NON_GOAL_SECTION_ANCHORS = (
    "cross-repo",
    "production live execution expansion",
    "replacement of existing `cryp` runtime guardrails",
)


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    assert start != -1, f"missing section start marker: {start_marker}"

    end = text.find(end_marker, start)
    assert end != -1, f"missing section end marker: {end_marker}"
    assert end > start, f"invalid section boundary: {start_marker} -> {end_marker}"

    return text[start:end]


def test_phase_37l_transport_contract_docs_exist() -> None:
    assert PRODUCER_CONTRACT_DOC.is_file(), (
        f"missing producer contract doc: {PRODUCER_CONTRACT_DOC}"
    )
    assert CONSUMER_CONTRACT_DOC.is_file(), (
        f"missing consumer contract doc: {CONSUMER_CONTRACT_DOC}"
    )


def test_phase_37l_transport_contract_key_anchor_parity() -> None:
    producer_text = PRODUCER_CONTRACT_DOC.read_text(encoding="utf-8")
    consumer_text = CONSUMER_CONTRACT_DOC.read_text(encoding="utf-8")

    missing_from_producer = [anchor for anchor in PARITY_ANCHORS if anchor not in producer_text]
    missing_from_consumer = [anchor for anchor in PARITY_ANCHORS if anchor not in consumer_text]

    assert not missing_from_producer, (
        "Phase 37L doc parity drift: anchors missing from producer doc: "
        + ", ".join(missing_from_producer)
    )
    assert not missing_from_consumer, (
        "Phase 37L doc parity drift: anchors missing from consumer doc: "
        + ", ".join(missing_from_consumer)
    )


def test_phase_37m_pickup_receipt_required_fields_section_parity() -> None:
    producer_text = PRODUCER_CONTRACT_DOC.read_text(encoding="utf-8")
    consumer_text = CONSUMER_CONTRACT_DOC.read_text(encoding="utf-8")

    producer_section = _extract_section(
        text=producer_text,
        start_marker="### Consumer pickup receipt (required for pickup)",
        end_marker="### Boundary response artifact (required; exactly one per attempt)",
    )
    consumer_section = _extract_section(
        text=consumer_text,
        start_marker="### Pickup receipt",
        end_marker="### Boundary response",
    )

    missing_from_producer = [
        anchor for anchor in PICKUP_RECEIPT_REQUIRED_FIELD_ANCHORS if anchor not in producer_section
    ]
    missing_from_consumer = [
        anchor for anchor in PICKUP_RECEIPT_REQUIRED_FIELD_ANCHORS if anchor not in consumer_section
    ]

    assert not missing_from_producer, (
        "Phase 37M section parity drift: pickup-field anchors missing from producer section: "
        + ", ".join(missing_from_producer)
    )
    assert not missing_from_consumer, (
        "Phase 37M section parity drift: pickup-field anchors missing from consumer section: "
        + ", ".join(missing_from_consumer)
    )


def test_phase_37m_idempotency_duplicate_rules_section_parity() -> None:
    producer_text = PRODUCER_CONTRACT_DOC.read_text(encoding="utf-8")
    consumer_text = CONSUMER_CONTRACT_DOC.read_text(encoding="utf-8")

    producer_section = _extract_section(
        text=producer_text,
        start_marker="## Duplicate / Retry / Idempotency Rules",
        end_marker="## Operator Workflow Steps (Local)",
    )
    consumer_section = _extract_section(
        text=consumer_text,
        start_marker="## Idempotency and Duplicate Handling",
        end_marker="## Preserved Boundaries and Non-Goals",
    )

    missing_from_producer = [
        anchor for anchor in IDEMPOTENCY_RULE_SECTION_ANCHORS if anchor not in producer_section
    ]
    missing_from_consumer = [
        anchor for anchor in IDEMPOTENCY_RULE_SECTION_ANCHORS if anchor not in consumer_section
    ]

    assert not missing_from_producer, (
        "Phase 37M section parity drift: idempotency anchors missing from producer section: "
        + ", ".join(missing_from_producer)
    )
    assert not missing_from_consumer, (
        "Phase 37M section parity drift: idempotency anchors missing from consumer section: "
        + ", ".join(missing_from_consumer)
    )


def test_phase_37m_non_goal_boundary_section_parity() -> None:
    producer_text = PRODUCER_CONTRACT_DOC.read_text(encoding="utf-8")
    consumer_text = CONSUMER_CONTRACT_DOC.read_text(encoding="utf-8")

    producer_section = _extract_section(
        text=producer_text,
        start_marker="## Explicit Non-Goals and Boundary Rules",
        end_marker="## Validation",
    )
    consumer_section = _extract_section(
        text=consumer_text,
        start_marker="## Preserved Boundaries and Non-Goals",
        end_marker="This document aligns local intake boundary behavior only.",
    )

    missing_from_producer = [
        anchor for anchor in NON_GOAL_SECTION_ANCHORS if anchor not in producer_section
    ]
    missing_from_consumer = [
        anchor for anchor in NON_GOAL_SECTION_ANCHORS if anchor not in consumer_section
    ]

    assert not missing_from_producer, (
        "Phase 37M section parity drift: non-goal anchors missing from producer section: "
        + ", ".join(missing_from_producer)
    )
    assert not missing_from_consumer, (
        "Phase 37M section parity drift: non-goal anchors missing from consumer section: "
        + ", ".join(missing_from_consumer)
    )
