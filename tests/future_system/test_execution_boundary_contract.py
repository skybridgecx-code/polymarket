from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.execution_boundary_contract import (
    ExecutionBoundaryHandoffRequest,
    validate_execution_boundary_handoff_request,
)


def _load_approved_handoff_fixture() -> dict[str, object]:
    fixture_path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "future_system"
        / "execution_boundary_contract"
        / "approved_handoff_request.json"
    )
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_validate_execution_boundary_handoff_request_accepts_approved_fixture() -> None:
    payload = _load_approved_handoff_fixture()

    validated = validate_execution_boundary_handoff_request(payload=payload)

    assert isinstance(validated, ExecutionBoundaryHandoffRequest)
    assert validated.contract_version == "37A.v1"
    assert validated.producer_system == "polymarket-arb"
    assert validated.consumer_system == "cryp"
    assert validated.handoff_payload.operator_decision == "approve"
    assert validated.handoff_payload.review_status == "decided"


def test_validate_execution_boundary_handoff_request_rejects_invalid_shape() -> None:
    payload = _load_approved_handoff_fixture()
    payload.pop("idempotency_key")

    with pytest.raises(ValueError, match="execution_boundary_contract_invalid_shape"):
        validate_execution_boundary_handoff_request(payload=payload)


def test_validate_execution_boundary_handoff_request_rejects_gate_failures() -> None:
    payload = _load_approved_handoff_fixture()
    payload["handoff_payload"]["operator_decision"] = "reject"

    with pytest.raises(
        ValueError,
        match="handoff_payload_operator_decision_not_approve",
    ):
        validate_execution_boundary_handoff_request(payload=payload)


def test_validate_handoff_request_rejects_correlation_or_idempotency_mismatch() -> None:
    payload = _load_approved_handoff_fixture()
    payload["correlation_id"] = "different_run_id"
    payload["idempotency_key"] = "bad:idempotency:key"

    with pytest.raises(
        ValueError,
        match="correlation_id_mismatch, idempotency_key_mismatch",
    ):
        validate_execution_boundary_handoff_request(payload=payload)


def test_validate_handoff_request_rejects_artifact_path_assumption_mismatch() -> None:
    payload = _load_approved_handoff_fixture()
    payload["handoff_payload"][
        "markdown_artifact_path"
    ] = "/tmp/future-system-operator-ui-demo/operator_runs/not_the_run_id.md"

    with pytest.raises(
        ValueError,
        match="markdown_artifact_path_invalid_for_run, artifact_markdown_file_path_mismatch",
    ):
        validate_execution_boundary_handoff_request(payload=payload)


def test_validate_handoff_request_can_require_local_files(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = tmp_path / "operator_runs"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    markdown_path = artifacts_root / f"{run_id}.md"
    json_path = artifacts_root / f"{run_id}.json"
    metadata_path = artifacts_root / f"{run_id}.operator_review.json"

    markdown_path.write_text("# local artifact\n", encoding="utf-8")
    json_path.write_text("{}", encoding="utf-8")
    metadata_path.write_text("{}", encoding="utf-8")

    payload = _load_approved_handoff_fixture()
    payload["handoff_payload"]["markdown_artifact_path"] = str(markdown_path)
    payload["handoff_payload"]["json_artifact_path"] = str(json_path)
    payload["handoff_payload"]["operator_review_metadata_path"] = str(metadata_path)
    payload["operator_review_metadata"]["artifact"]["markdown_file_path"] = str(markdown_path)
    payload["operator_review_metadata"]["artifact"]["json_file_path"] = str(json_path)

    assert validate_execution_boundary_handoff_request(
        payload=payload,
        require_local_artifacts=True,
    ).handoff_payload.run_id == run_id


def test_validate_execution_boundary_handoff_request_requires_local_files_when_requested(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = tmp_path / "operator_runs"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    markdown_path = artifacts_root / f"{run_id}.md"
    markdown_path.write_text("# only one file\n", encoding="utf-8")

    payload = _load_approved_handoff_fixture()
    payload["handoff_payload"]["markdown_artifact_path"] = str(markdown_path)
    payload["handoff_payload"]["json_artifact_path"] = str(artifacts_root / f"{run_id}.json")
    payload["handoff_payload"]["operator_review_metadata_path"] = str(
        artifacts_root / f"{run_id}.operator_review.json"
    )
    payload["operator_review_metadata"]["artifact"]["markdown_file_path"] = str(markdown_path)
    payload["operator_review_metadata"]["artifact"]["json_file_path"] = str(
        artifacts_root / f"{run_id}.json"
    )

    with pytest.raises(
        ValueError,
        match="missing_local_file:json_artifact:|missing_local_file:operator_review_metadata:",
    ):
        validate_execution_boundary_handoff_request(
            payload=payload,
            require_local_artifacts=True,
        )
