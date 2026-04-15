"""Deterministic tests for operator review metadata update/write helper contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from future_system.operator_review_models import (
    OperatorReviewDecisionRecord,
    OperatorReviewDecisionUpdateInput,
    apply_operator_review_decision_update,
    render_operator_review_decision_record_json,
    update_existing_operator_review_metadata_companion,
)


def test_apply_update_pending_clears_decision_and_decided_timestamp() -> None:
    existing = _existing_decided_record()

    updated = apply_operator_review_decision_update(
        existing_record=existing,
        update_input=OperatorReviewDecisionUpdateInput(
            review_status="pending",
            operator_decision="reject",
            review_notes_summary="Needs another pass.",
            reviewer_identity="operator_b",
            updated_at_epoch_ns=2_000,
        ),
    )

    assert updated.review_status == "pending"
    assert updated.operator_decision is None
    assert updated.decided_at_epoch_ns is None
    assert updated.updated_at_epoch_ns == 2_000


def test_apply_update_decided_requires_operator_decision() -> None:
    existing = _existing_pending_record()

    with pytest.raises(ValueError, match="operator_decision is required"):
        apply_operator_review_decision_update(
            existing_record=existing,
            update_input=OperatorReviewDecisionUpdateInput(
                review_status="decided",
                review_notes_summary="Decision attempted without decision value.",
                reviewer_identity="operator_c",
                updated_at_epoch_ns=5_000,
            ),
        )


def test_apply_update_decided_sets_and_then_keeps_decided_timestamp_deterministically() -> None:
    existing = _existing_pending_record()

    first = apply_operator_review_decision_update(
        existing_record=existing,
        update_input=OperatorReviewDecisionUpdateInput(
            review_status="decided",
            operator_decision="approve",
            review_notes_summary="Approved after review.",
            reviewer_identity="operator_a",
            updated_at_epoch_ns=10_000,
        ),
    )
    second = apply_operator_review_decision_update(
        existing_record=first,
        update_input=OperatorReviewDecisionUpdateInput(
            review_status="decided",
            operator_decision="needs_follow_up",
            review_notes_summary="Escalating for follow-up despite initial approval.",
            reviewer_identity="operator_d",
            updated_at_epoch_ns=11_000,
        ),
    )

    assert first.decided_at_epoch_ns == 10_000
    assert first.updated_at_epoch_ns == 10_000
    assert second.decided_at_epoch_ns == 10_000
    assert second.updated_at_epoch_ns == 11_000


def test_update_helper_preserves_non_editable_fields(tmp_path: Path) -> None:
    existing = _existing_pending_record()
    path = tmp_path / f"{existing.artifact.run_id}.operator_review.json"
    path.write_text(render_operator_review_decision_record_json(existing), encoding="utf-8")

    updated = update_existing_operator_review_metadata_companion(
        target_directory=tmp_path,
        run_id=existing.artifact.run_id,
        update_input=OperatorReviewDecisionUpdateInput(
            review_status="decided",
            operator_decision="reject",
            review_notes_summary="Rejected after operator review.",
            reviewer_identity="operator_b",
            updated_at_epoch_ns=12_000,
        ),
    )

    assert updated.record_kind == existing.record_kind
    assert updated.record_version == existing.record_version
    assert updated.artifact == existing.artifact
    assert updated.run_flags_snapshot == existing.run_flags_snapshot


def test_update_helper_rejects_missing_companion_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="operator_review_metadata_missing"):
        update_existing_operator_review_metadata_companion(
            target_directory=tmp_path,
            run_id="theme_ctx_strong.analysis_success_export",
            update_input=OperatorReviewDecisionUpdateInput(
                review_status="pending",
                review_notes_summary="No file exists.",
                reviewer_identity="operator_a",
                updated_at_epoch_ns=1,
            ),
        )


def test_update_helper_rejects_malformed_companion_file(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    (tmp_path / f"{run_id}.operator_review.json").write_text("{malformed", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed JSON content"):
        update_existing_operator_review_metadata_companion(
            target_directory=tmp_path,
            run_id=run_id,
            update_input=OperatorReviewDecisionUpdateInput(
                review_status="pending",
                review_notes_summary="Malformed should fail.",
                reviewer_identity="operator_a",
                updated_at_epoch_ns=2,
            ),
        )


def test_update_helper_rejects_out_of_root_companion_path(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    outside_target = tmp_path.parent / f"{run_id}.operator_review.json"
    outside_target.write_text(
        render_operator_review_decision_record_json(_existing_pending_record()),
        encoding="utf-8",
    )
    (tmp_path / f"{run_id}.operator_review.json").symlink_to(outside_target)

    with pytest.raises(ValueError, match="out_of_bounds"):
        update_existing_operator_review_metadata_companion(
            target_directory=tmp_path,
            run_id=run_id,
            update_input=OperatorReviewDecisionUpdateInput(
                review_status="pending",
                review_notes_summary="Out of root should fail.",
                reviewer_identity="operator_a",
                updated_at_epoch_ns=3,
            ),
        )


def test_update_helper_rejects_non_file_targets(tmp_path: Path) -> None:
    run_id = "theme_ctx_strong.analysis_success_export"
    (tmp_path / f"{run_id}.operator_review.json").mkdir()

    with pytest.raises(ValueError, match="must be a regular file"):
        update_existing_operator_review_metadata_companion(
            target_directory=tmp_path,
            run_id=run_id,
            update_input=OperatorReviewDecisionUpdateInput(
                review_status="pending",
                review_notes_summary="Directory target should fail.",
                reviewer_identity="operator_a",
                updated_at_epoch_ns=4,
            ),
        )


def test_update_helper_writes_stable_deterministic_json_shape(tmp_path: Path) -> None:
    existing = _existing_pending_record()
    run_id = existing.artifact.run_id
    companion_path = tmp_path / f"{run_id}.operator_review.json"
    companion_path.write_text(
        render_operator_review_decision_record_json(existing),
        encoding="utf-8",
    )

    updated = update_existing_operator_review_metadata_companion(
        target_directory=tmp_path,
        run_id=run_id,
        update_input=OperatorReviewDecisionUpdateInput(
            review_status="decided",
            operator_decision="approve",
            review_notes_summary="Approved with stable deterministic serialization.",
            reviewer_identity="operator_a",
            updated_at_epoch_ns=99_000,
        ),
    )

    assert (
        companion_path.read_text(encoding="utf-8")
        == render_operator_review_decision_record_json(updated)
    )


def _existing_pending_record() -> OperatorReviewDecisionRecord:
    return OperatorReviewDecisionRecord.model_validate(
        {
            "record_kind": "operator_review_decision_record",
            "record_version": 1,
            "artifact": {
                "run_id": "theme_ctx_strong.analysis_success_export",
                "theme_id": "theme_ctx_strong",
                "status": "success",
                "export_kind": "analysis_success_export",
                "failure_stage": None,
                "json_file_path": "/tmp/theme_ctx_strong.analysis_success_export.json",
                "markdown_file_path": "/tmp/theme_ctx_strong.analysis_success_export.md",
            },
            "review_status": "pending",
            "operator_decision": None,
            "review_notes_summary": "Initial operator notes.",
            "reviewer_identity": "operator_a",
            "decided_at_epoch_ns": None,
            "updated_at_epoch_ns": 1_000,
            "run_flags_snapshot": ["analysis_dry_run", "policy_computed"],
        }
    )


def _existing_decided_record() -> OperatorReviewDecisionRecord:
    return OperatorReviewDecisionRecord.model_validate(
        {
            "record_kind": "operator_review_decision_record",
            "record_version": 1,
            "artifact": {
                "run_id": "theme_ctx_strong.analysis_success_export",
                "theme_id": "theme_ctx_strong",
                "status": "success",
                "export_kind": "analysis_success_export",
                "failure_stage": None,
                "json_file_path": "/tmp/theme_ctx_strong.analysis_success_export.json",
                "markdown_file_path": "/tmp/theme_ctx_strong.analysis_success_export.md",
            },
            "review_status": "decided",
            "operator_decision": "approve",
            "review_notes_summary": "Approved after operator review.",
            "reviewer_identity": "operator_a",
            "decided_at_epoch_ns": 1_500,
            "updated_at_epoch_ns": 1_500,
            "run_flags_snapshot": ["analysis_dry_run", "policy_computed"],
        }
    )
