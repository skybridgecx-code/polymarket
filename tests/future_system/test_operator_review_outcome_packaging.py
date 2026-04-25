from __future__ import annotations

import json
from pathlib import Path

import pytest
from future_system.review_outcome_packaging import write_review_outcome_package


def test_write_review_outcome_package_creates_markdown_and_json(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    markdown_path = tmp_path / f"{run_id}.md"
    json_path = tmp_path / f"{run_id}.json"
    metadata_path = tmp_path / f"{run_id}.operator_review.json"
    target_root = tmp_path / "packages"

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

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=target_root,
    )

    package_dir = target_root / f"{run_id}.package"
    summary_path = package_dir / "handoff_summary.md"
    payload_path = package_dir / "handoff_payload.json"

    assert package_dir.is_dir()
    assert summary_path.is_file()
    assert payload_path.is_file()

    summary_text = summary_path.read_text(encoding="utf-8")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    assert run_id in summary_text
    assert "Approved for handoff." in summary_text
    assert payload["run_id"] == run_id
    assert payload["review_status"] == "decided"
    assert payload["operator_decision"] == "approve"
    assert payload["review_notes_summary"] == "Approved for handoff."
    assert payload["reviewer_identity"] == "operator_a"
    assert payload["package_version"] == "v1"
    assert package.payload.run_id == run_id


def test_write_review_outcome_package_preserves_cryp_confirmation_signal(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    markdown_path = tmp_path / f"{run_id}.md"
    json_path = tmp_path / f"{run_id}.json"
    metadata_path = tmp_path / f"{run_id}.operator_review.json"
    target_root = tmp_path / "packages"

    markdown_path.write_text("# review artifact\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "entry_kind": "analysis_success_review_entry",
                "cryp_external_confirmation_signal": {
                    "asset": "BTC",
                    "signal": "buy",
                    "confidence_adjustment": 0.12,
                    "rationale": "Structured reviewed signal.",
                    "source_system": "polymarket-arb",
                    "supporting_tags": ["polymarket", "reviewed"],
                },
            },
            indent=2,
        ),
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
                "decided_at_epoch_ns": 1700000000000000001,
                "updated_at_epoch_ns": 1700000000000000002,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=target_root,
    )

    payload_path = target_root / f"{run_id}.package" / "handoff_payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    signal = payload["cryp_external_confirmation_signal"]

    assert signal == {
        "asset": "BTC",
        "confidence_adjustment": 0.12,
        "correlation_id": run_id,
        "observed_at_epoch_ns": 1700000000000000002,
        "rationale": "Structured reviewed signal.",
        "signal": "buy",
        "source_system": "polymarket-arb",
        "supporting_tags": ["polymarket", "reviewed"],
    }
    assert package.payload.cryp_external_confirmation_signal == signal


def test_write_review_outcome_package_fails_when_metadata_missing(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    markdown_path = tmp_path / f"{run_id}.md"
    json_path = tmp_path / f"{run_id}.json"
    metadata_path = tmp_path / f"{run_id}.operator_review.json"

    markdown_path.write_text("# review artifact\n", encoding="utf-8")
    json_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="missing_operator_review_metadata"):
        write_review_outcome_package(
            run_id=run_id,
            markdown_artifact_path=markdown_path,
            json_artifact_path=json_path,
            operator_review_metadata_path=metadata_path,
            target_root=tmp_path / "packages",
        )


def test_write_review_outcome_package_fails_on_run_id_mismatch(
    tmp_path: Path,
) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    markdown_path = tmp_path / f"{run_id}.md"
    json_path = tmp_path / f"{run_id}.json"
    metadata_path = tmp_path / f"{run_id}.operator_review.json"

    markdown_path.write_text("# review artifact\n", encoding="utf-8")
    json_path.write_text("{}", encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": "wrong_run_id",
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_ctx_strong",
                    "failure_stage": None,
                },
                "review_status": "pending",
                "operator_decision": None,
                "review_notes_summary": None,
                "reviewer_identity": None,
                "run_flags_snapshot": [],
                "decided_at_epoch_ns": None,
                "updated_at_epoch_ns": None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="run_id mismatch"):
        write_review_outcome_package(
            run_id=run_id,
            markdown_artifact_path=markdown_path,
            json_artifact_path=json_path,
            operator_review_metadata_path=metadata_path,
            target_root=tmp_path / "packages",
        )
