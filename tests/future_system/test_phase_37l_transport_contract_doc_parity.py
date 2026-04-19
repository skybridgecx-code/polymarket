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
