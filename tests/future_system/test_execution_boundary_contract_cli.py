from __future__ import annotations

import json
from pathlib import Path

from future_system.cli.execution_boundary_intake import main


def _load_approved_handoff_fixture() -> dict[str, object]:
    fixture_path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "future_system"
        / "execution_boundary_contract"
        / "approved_handoff_request.json"
    )
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_execution_boundary_intake_cli_writes_ack_for_valid_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    payload = _load_approved_handoff_fixture()
    run_id = str(payload["correlation_id"])

    handoff_request_path = tmp_path / "handoff_request.json"
    handoff_request_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    export_root = tmp_path / "exports"

    exit_code = main(
        [
            "--handoff-request-path",
            str(handoff_request_path),
            "--export-root",
            str(export_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    expected_ack_path = export_root / f"{run_id}.execution_boundary_ack.json"
    assert summary["result_kind"] == "execution_boundary_intake_result"
    assert summary["status"] == "accepted"
    assert summary["accepted"] is True
    assert summary["ack_artifact_path"] == str(expected_ack_path)
    assert summary["reject_artifact_path"] is None

    ack_payload = json.loads(expected_ack_path.read_text(encoding="utf-8"))
    assert ack_payload["artifact_kind"] == "execution_boundary_intake_ack"
    assert ack_payload["correlation_id"] == run_id
    assert ack_payload["idempotency_key"] == payload["idempotency_key"]


def test_execution_boundary_intake_cli_writes_reject_for_invalid_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    payload = _load_approved_handoff_fixture()
    payload["handoff_payload"]["operator_decision"] = "reject"
    run_id = str(payload["correlation_id"])

    handoff_request_path = tmp_path / "handoff_request.json"
    handoff_request_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    export_root = tmp_path / "exports"

    exit_code = main(
        [
            "--handoff-request-path",
            str(handoff_request_path),
            "--export-root",
            str(export_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    expected_reject_path = export_root / f"{run_id}.execution_boundary_reject.json"
    assert summary["result_kind"] == "execution_boundary_intake_result"
    assert summary["status"] == "rejected"
    assert summary["accepted"] is False
    assert summary["ack_artifact_path"] is None
    assert summary["reject_artifact_path"] == str(expected_reject_path)

    reject_payload = json.loads(expected_reject_path.read_text(encoding="utf-8"))
    assert reject_payload["artifact_kind"] == "execution_boundary_intake_reject"
    assert (
        "handoff_payload_operator_decision_not_approve"
        in reject_payload["reason_codes"]
    )
