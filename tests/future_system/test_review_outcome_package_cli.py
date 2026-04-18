from __future__ import annotations

import json
from pathlib import Path

from future_system.cli.review_outcome_package import main


def _write_reviewed_run_fixture(tmp_path: Path, *, run_id: str) -> Path:
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
                "decided_at_epoch_ns": 1,
                "updated_at_epoch_ns": 1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return artifacts_root


def test_review_outcome_package_cli_writes_package_and_prints_paths(
    tmp_path: Path,
    capsys,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_reviewed_run_fixture(tmp_path, run_id=run_id)
    target_root = tmp_path / "packages"

    exit_code = main(
        [
            "--run-id",
            run_id,
            "--artifacts-root",
            str(artifacts_root),
            "--target-root",
            str(target_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert f"run_id: {run_id}" in captured.out
    assert "package_dir:" in captured.out
    assert "handoff_summary_path:" in captured.out
    assert "handoff_payload_path:" in captured.out

    package_dir = target_root / f"{run_id}.package"
    assert package_dir.is_dir()
    assert (package_dir / "handoff_summary.md").is_file()
    assert (package_dir / "handoff_payload.json").is_file()


def test_review_outcome_package_cli_defaults_target_root_to_artifacts_root(
    tmp_path: Path,
    capsys,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = _write_reviewed_run_fixture(tmp_path, run_id=run_id)

    exit_code = main(
        [
            "--run-id",
            run_id,
            "--artifacts-root",
            str(artifacts_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    package_dir = artifacts_root / f"{run_id}.package"
    assert package_dir.is_dir()


def test_review_outcome_package_cli_returns_nonzero_on_missing_metadata(
    tmp_path: Path,
    capsys,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    (artifacts_root / f"{run_id}.md").write_text("# review artifact\n", encoding="utf-8")
    (artifacts_root / f"{run_id}.json").write_text("{}", encoding="utf-8")

    exit_code = main(
        [
            "--run-id",
            run_id,
            "--artifacts-root",
            str(artifacts_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "review_outcome_package_cli_error:" in captured.err
    assert "missing_operator_review_metadata" in captured.err
