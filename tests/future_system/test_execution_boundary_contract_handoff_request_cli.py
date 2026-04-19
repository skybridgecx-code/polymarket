from __future__ import annotations

import json
from pathlib import Path

from future_system.cli.execution_boundary_handoff_request import main
from future_system.review_outcome_packaging import write_review_outcome_package


def _write_reviewed_run_package(tmp_path: Path, *, run_id: str) -> Path:
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
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_ctx_strong",
                    "failure_stage": None,
                },
                "review_status": "decided",
                "operator_decision": "approve",
                "review_notes_summary": "Approved for handoff.",
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

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=tmp_path / "packages",
    )
    return Path(package.paths.package_dir)


def test_execution_boundary_handoff_request_cli_writes_default_handoff_request_path(
    tmp_path: Path,
    capsys,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    package_dir = _write_reviewed_run_package(tmp_path, run_id=run_id)

    exit_code = main(["--package-dir", str(package_dir)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    expected_path = package_dir / "handoff_request.json"
    assert summary["result_kind"] == "execution_boundary_handoff_request_build_result"
    assert summary["status"] == "built"
    assert summary["package_dir"] == str(package_dir)
    assert summary["handoff_request_path"] == str(expected_path)
    assert expected_path.is_file()

    envelope = json.loads(expected_path.read_text(encoding="utf-8"))
    assert envelope["correlation_id"] == run_id
    assert envelope["idempotency_key"] == f"{run_id}:1700000000000000001:approve"


def test_execution_boundary_handoff_request_cli_supports_explicit_output_path(
    tmp_path: Path,
    capsys,
) -> None:
    package_dir = _write_reviewed_run_package(
        tmp_path,
        run_id="theme_ctx_strong.analysis_success_export",
    )
    output_path = tmp_path / "exports" / "custom_handoff_request.json"

    exit_code = main(
        [
            "--package-dir",
            str(package_dir),
            "--output-path",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""

    summary = json.loads(captured.out)
    assert summary["handoff_request_path"] == str(output_path)
    assert output_path.is_file()


def test_execution_boundary_handoff_request_cli_returns_nonzero_on_invalid_package(
    tmp_path: Path,
    capsys,
) -> None:
    package_dir = tmp_path / "broken.package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "handoff_summary.md").write_text("# summary\n", encoding="utf-8")

    exit_code = main(["--package-dir", str(package_dir)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "execution_boundary_handoff_request_cli_error:" in captured.err
    assert "missing_handoff_payload" in captured.err
