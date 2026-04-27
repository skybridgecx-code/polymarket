from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.cli.execution_boundary_dispatch import main as dispatch_cli_main
from future_system.execution_boundary_contract import dispatch_execution_boundary_handoff_request


def _write_review_artifacts(
    tmp_path: Path,
    *,
    run_id: str,
    run_status: str = "success",
    review_status: str = "decided",
    operator_decision: str | None = "approve",
) -> Path:
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    markdown_path = artifacts_root / f"{run_id}.md"
    json_path = artifacts_root / f"{run_id}.json"
    metadata_path = artifacts_root / f"{run_id}.operator_review.json"

    markdown_path.write_text("# review artifact\n", encoding="utf-8")
    json_path.write_text(
        json.dumps({"entry_kind": "analysis_success_review_entry"}, indent=2),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": run_id,
                    "status": run_status,
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_ctx_strong",
                    "failure_stage": None,
                },
                "review_status": review_status,
                "operator_decision": operator_decision,
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
    return artifacts_root


def test_dispatch_writes_canonical_inbound_and_dispatch_receipt(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_review_artifacts(tmp_path, run_id=run_id)
    cryp_transport_root = tmp_path / "cryp_transport"

    result = dispatch_execution_boundary_handoff_request(
        run_id=run_id,
        artifacts_root=artifacts_root,
        cryp_transport_root=cryp_transport_root,
        attempt_id="attempt-000001",
        dry_run=False,
        dispatched_at_epoch_ns=1700000000000000099,
    )

    expected_handoff_request_path = (
        cryp_transport_root / "inbound" / run_id / "attempt-000001" / "handoff_request.json"
    ).resolve()
    expected_receipt_path = (
        cryp_transport_root
        / "dispatch"
        / run_id
        / "attempt-000001"
        / "polymarket_arb_dispatch_receipt.json"
    ).resolve()

    assert result.status == "dispatched_to_cryp_inbound"
    assert result.correlation_id == run_id
    assert result.attempt_id == "attempt-000001"
    assert result.resolved_inbound_handoff_request_path == str(expected_handoff_request_path)
    assert result.dispatch_receipt_path == str(expected_receipt_path)
    assert expected_handoff_request_path.is_file()
    assert expected_receipt_path.is_file()

    dispatched_payload = json.loads(expected_handoff_request_path.read_text(encoding="utf-8"))
    assert dispatched_payload["correlation_id"] == run_id
    assert dispatched_payload["idempotency_key"] == f"{run_id}:1700000000000000001:approve"

    receipt_payload = json.loads(expected_receipt_path.read_text(encoding="utf-8"))
    assert receipt_payload["status"] == "dispatched_to_cryp_inbound"
    assert receipt_payload["attempt_id"] == "attempt-000001"
    assert receipt_payload["dispatched_at_epoch_ns"] == 1700000000000000099


def test_dispatch_dry_run_does_not_write_into_cryp_inbound(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_review_artifacts(tmp_path, run_id=run_id)
    cryp_transport_root = tmp_path / "cryp_transport"

    result = dispatch_execution_boundary_handoff_request(
        run_id=run_id,
        artifacts_root=artifacts_root,
        cryp_transport_root=cryp_transport_root,
        attempt_id="attempt-000002",
        dry_run=True,
    )

    assert result.status == "dry_run_validated_only"
    assert result.dry_run is True
    assert (
        cryp_transport_root / "inbound" / run_id / "attempt-000002" / "handoff_request.json"
    ).exists() is False
    assert (
        cryp_transport_root
        / "dispatch"
        / run_id
        / "attempt-000002"
        / "polymarket_arb_dispatch_receipt.json"
    ).exists() is False


def test_dispatch_rejects_invalid_package_before_dispatch(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_review_artifacts(
        tmp_path,
        run_id=run_id,
        run_status="success",
        review_status="decided",
        operator_decision="reject",
    )
    cryp_transport_root = tmp_path / "cryp_transport"

    with pytest.raises(ValueError, match="execution_boundary_contract_invalid"):
        dispatch_execution_boundary_handoff_request(
            run_id=run_id,
            artifacts_root=artifacts_root,
            cryp_transport_root=cryp_transport_root,
            attempt_id="attempt-000003",
            dry_run=False,
        )

    assert (
        cryp_transport_root / "inbound" / run_id / "attempt-000003" / "handoff_request.json"
    ).exists() is False


def test_dispatch_generated_attempt_id_is_deterministic_epoch_ns_and_canonical(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_review_artifacts(tmp_path, run_id=run_id)
    cryp_transport_root = tmp_path / "cryp_transport"

    result = dispatch_execution_boundary_handoff_request(
        run_id=run_id,
        artifacts_root=artifacts_root,
        cryp_transport_root=cryp_transport_root,
        attempt_id=None,
        dry_run=True,
        generated_attempt_epoch_ns=1700000000000000123,
    )

    assert result.attempt_id == "attempt-1700000000000000123"
    assert result.resolved_inbound_handoff_request_path.endswith(
        f"/inbound/{run_id}/attempt-1700000000000000123/handoff_request.json"
    )


def test_execution_boundary_dispatch_cli_dry_run_prints_resolved_paths(
    tmp_path: Path,
    capsys,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_review_artifacts(tmp_path, run_id=run_id)
    cryp_transport_root = tmp_path / "cryp_transport"

    exit_code = dispatch_cli_main(
        [
            "--run-id",
            run_id,
            "--artifacts-root",
            str(artifacts_root),
            "--cryp-transport-root",
            str(cryp_transport_root),
            "--attempt-id",
            "attempt-000004",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    summary = json.loads(captured.out)
    assert summary["status"] == "dry_run_validated_only"
    assert summary["attempt_id"] == "attempt-000004"
    assert summary["validation_status"] == "passed"
