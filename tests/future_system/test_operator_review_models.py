"""Deterministic tests for operator review decision metadata contracts."""

from __future__ import annotations

import pytest
from future_system.operator_review_models.builder import (
    build_initial_operator_review_decision_record,
)
from future_system.operator_review_models.models import (
    OperatorReviewArtifactReference,
    OperatorReviewDecisionRecord,
)


def test_operator_review_decision_record_pending_serialization_is_bounded_and_deterministic(
) -> None:
    record = OperatorReviewDecisionRecord(
        artifact=OperatorReviewArtifactReference(
            run_id="theme_ctx_strong.analysis_success_export",
            theme_id="theme_ctx_strong",
            status="success",
            export_kind="analysis_success_export",
            json_file_path="/tmp/theme_ctx_strong.analysis_success_export.json",
            markdown_file_path="/tmp/theme_ctx_strong.analysis_success_export.md",
        ),
        review_status="pending",
        run_flags_snapshot=["analysis_dry_run", "analysis_dry_run", "policy_computed"],
    )

    assert record.record_kind == "operator_review_decision_record"
    assert record.record_version == 1
    assert record.review_status == "pending"
    assert record.operator_decision is None
    assert record.run_flags_snapshot == ["analysis_dry_run", "policy_computed"]
    assert record.model_dump(mode="json") == {
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
        "review_notes_summary": None,
        "reviewer_identity": None,
        "decided_at_epoch_ns": None,
        "updated_at_epoch_ns": None,
        "run_flags_snapshot": ["analysis_dry_run", "policy_computed"],
    }


def test_operator_review_decision_record_decided_requires_decision_and_preserves_stage() -> None:
    record = OperatorReviewDecisionRecord(
        artifact=OperatorReviewArtifactReference(
            run_id="theme_ctx_strong.analysis_failure_export.reasoning_parse",
            theme_id="theme_ctx_strong",
            status="failed",
            export_kind="analysis_failure_export",
            failure_stage="reasoning_parse",
        ),
        review_status="decided",
        operator_decision="needs_follow_up",
        review_notes_summary="Escalate for analyst prompt quality review.",
        reviewer_identity="operator_a",
        decided_at_epoch_ns=1_900_000_000_000_000_000,
        updated_at_epoch_ns=1_900_000_000_000_000_001,
    )

    assert record.review_status == "decided"
    assert record.operator_decision == "needs_follow_up"
    assert record.artifact.failure_stage == "reasoning_parse"


def test_operator_review_decision_record_rejects_invalid_status_decision_combinations() -> None:
    with pytest.raises(ValueError, match="must not set operator_decision"):
        OperatorReviewDecisionRecord(
            artifact=OperatorReviewArtifactReference(
                run_id="theme_ctx_strong.analysis_success_export",
                theme_id="theme_ctx_strong",
                status="success",
                export_kind="analysis_success_export",
            ),
            review_status="pending",
            operator_decision="approve",
        )

    with pytest.raises(ValueError, match="requires operator_decision"):
        OperatorReviewDecisionRecord(
            artifact=OperatorReviewArtifactReference(
                run_id="theme_ctx_strong.analysis_success_export",
                theme_id="theme_ctx_strong",
                status="success",
                export_kind="analysis_success_export",
            ),
            review_status="decided",
        )


def test_operator_review_artifact_reference_rejects_invalid_status_failure_stage_alignment(
) -> None:
    with pytest.raises(ValueError, match="must be None when status is success"):
        OperatorReviewArtifactReference(
            run_id="theme_ctx_strong.analysis_success_export",
            theme_id="theme_ctx_strong",
            status="success",
            export_kind="analysis_success_export",
            failure_stage="analyst_timeout",
        )

    with pytest.raises(ValueError, match="required when status is failed"):
        OperatorReviewArtifactReference(
            run_id="theme_ctx_strong.analysis_failure_export.analyst_timeout",
            theme_id="theme_ctx_strong",
            status="failed",
            export_kind="analysis_failure_export",
        )


def test_build_initial_operator_review_decision_record_from_success_artifact_payload() -> None:
    artifact_payload = {
        "theme_id": "theme_ctx_strong",
        "status": "success",
        "export_kind": "analysis_success_export",
        "run_flags": ["analysis_dry_run", "analysis_dry_run", "policy_computed"],
        "payload": {
            "export_kind": "analysis_success_export",
            "status": "success",
            "theme_id": "theme_ctx_strong",
        },
    }

    record = build_initial_operator_review_decision_record(
        run_id="theme_ctx_strong.analysis_success_export",
        artifact_payload=artifact_payload,
        json_file_path="/tmp/theme_ctx_strong.analysis_success_export.json",
        markdown_file_path="/tmp/theme_ctx_strong.analysis_success_export.md",
    )

    assert record.review_status == "pending"
    assert record.operator_decision is None
    assert record.artifact.status == "success"
    assert record.artifact.export_kind == "analysis_success_export"
    assert record.artifact.failure_stage is None
    assert record.run_flags_snapshot == ["analysis_dry_run", "policy_computed"]


def test_build_initial_operator_review_decision_record_from_failure_payload_fallback_export_kind(
) -> None:
    artifact_payload = {
        "theme_id": "theme_ctx_strong",
        "status": "failed",
        "payload": {
            "export_kind": "analysis_failure_export",
            "status": "failed",
            "theme_id": "theme_ctx_strong",
            "failure_stage": "analyst_transport",
            "run_flags": ["analysis_dry_run", "analyst_transport_failed"],
        },
    }

    record = build_initial_operator_review_decision_record(
        run_id="theme_ctx_strong.analysis_failure_export.analyst_transport",
        artifact_payload=artifact_payload,
    )

    assert record.review_status == "pending"
    assert record.artifact.status == "failed"
    assert record.artifact.export_kind == "analysis_failure_export"
    assert record.artifact.failure_stage == "analyst_transport"
    assert record.run_flags_snapshot == ["analysis_dry_run", "analyst_transport_failed"]


def test_build_initial_operator_review_decision_record_rejects_failed_artifact_without_stage(
) -> None:
    artifact_payload = {
        "theme_id": "theme_ctx_strong",
        "status": "failed",
        "payload": {
            "export_kind": "analysis_failure_export",
            "status": "failed",
            "theme_id": "theme_ctx_strong",
        },
    }

    with pytest.raises(ValueError, match="failure_stage"):
        build_initial_operator_review_decision_record(
            run_id="theme_ctx_strong.analysis_failure_export.missing_stage",
            artifact_payload=artifact_payload,
        )
