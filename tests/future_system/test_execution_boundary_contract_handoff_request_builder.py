from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.execution_boundary_contract import (
    ExecutionBoundaryHandoffRequest,
    validate_execution_boundary_handoff_request,
    write_execution_boundary_handoff_request_from_package,
)
from future_system.review_outcome_packaging import write_review_outcome_package


def _write_reviewed_run_package(tmp_path: Path, *, run_id: str) -> Path:
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    markdown_path = artifacts_root / f"{run_id}.md"
    json_path = artifacts_root / f"{run_id}.json"
    metadata_path = artifacts_root / f"{run_id}.operator_review.json"

    markdown_path.write_text("# review artifact\n", encoding="utf-8")
    json_path.write_text(
        json.dumps({"entry_kind": "analysis_success_review_entry"}, sort_keys=True),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": run_id,
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_ctx_strong",
                    "failure_stage": None,
                },
                "review_status": "decided",
                "operator_decision": "approve",
                "review_notes_summary": "Approved for bounded handoff.",
                "reviewer_identity": "operator_a",
                "run_flags_snapshot": [],
                "decided_at_epoch_ns": 1700000000000000000,
                "updated_at_epoch_ns": 1700000000000000001,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    target_root = tmp_path / "packages"
    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=target_root,
    )

    return Path(package.paths.package_dir)


def test_write_handoff_request_from_package_writes_valid_deterministic_envelope(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    package_dir = _write_reviewed_run_package(tmp_path, run_id=run_id)

    output_path = write_execution_boundary_handoff_request_from_package(
        package_dir=package_dir
    )

    assert output_path == package_dir / "handoff_request.json"
    assert output_path.is_file()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    envelope = ExecutionBoundaryHandoffRequest.model_validate(payload)
    validated = validate_execution_boundary_handoff_request(
        payload=payload,
        require_local_artifacts=True,
    )

    assert validated.correlation_id == run_id
    assert envelope.correlation_id == run_id
    assert envelope.idempotency_key == f"{run_id}:1700000000000000001:approve"
    assert envelope.package_artifact_path == str(package_dir)
    assert envelope.handoff_payload_path == str(package_dir / "handoff_payload.json")
    assert envelope.handoff_summary_path == str(package_dir / "handoff_summary.md")


def test_write_handoff_request_from_package_fails_when_handoff_payload_missing(
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "missing-payload.package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "handoff_summary.md").write_text("# summary\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing_handoff_payload"):
        write_execution_boundary_handoff_request_from_package(package_dir=package_dir)


def test_write_handoff_request_from_package_fails_when_metadata_is_incomplete(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    package_dir = _write_reviewed_run_package(tmp_path, run_id=run_id)

    payload_path = package_dir / "handoff_payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    metadata_path = Path(payload["operator_review_metadata_path"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["updated_at_epoch_ns"] = None
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="handoff_request_builder_missing_updated_at_epoch_ns"):
        write_execution_boundary_handoff_request_from_package(package_dir=package_dir)
