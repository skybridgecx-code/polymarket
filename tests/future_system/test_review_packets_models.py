"""Model validation tests for future_system.review_packets contracts."""

from __future__ import annotations

import pytest
from future_system.review_packets.models import (
    AnalysisFailureReviewPacket,
    AnalysisReviewPacketEnvelope,
    AnalysisSuccessReviewPacket,
)
from pydantic import ValidationError


def test_review_packet_models_accept_valid_success_and_failure_payloads() -> None:
    success = AnalysisSuccessReviewPacket.model_validate(
        {
            "packet_kind": "analysis_success",
            "status": "success",
            "theme_id": "theme_review_success",
            "run_flags": ["analysis_dry_run", "policy_computed"],
            "summary_text": (
                "theme_id=theme_review_success; packet_kind=analysis_success; status=success; "
                "candidate_posture=candidate; reasoning_posture=candidate; "
                "policy_decision=allow; run_flags=analysis_dry_run,policy_computed."
            ),
            "runtime_summary": "theme_id=theme_review_success; policy_decision=allow.",
            "candidate_posture": "candidate",
            "reasoning_posture": "candidate",
            "policy_decision": "allow",
            "decision_score": 0.812,
            "readiness_score": 0.744,
            "risk_penalty": 0.232,
        }
    )
    failure = AnalysisFailureReviewPacket.model_validate(
        {
            "packet_kind": "analysis_failure",
            "status": "failed",
            "theme_id": "theme_review_failure",
            "failure_stage": "analyst_transport",
            "run_flags": ["analysis_dry_run", "analyst_transport_failed"],
            "summary_text": (
                "theme_id=theme_review_failure; packet_kind=analysis_failure; status=failed; "
                "failure_stage=analyst_transport; "
                "run_flags=analysis_dry_run,analyst_transport_failed."
            ),
            "runtime_summary": (
                "theme_id=theme_review_failure; status=failed; "
                "failure_stage=analyst_transport; "
                "run_flags=analysis_dry_run,analyst_transport_failed."
            ),
            "error_message": "analysis_run_failed: stage=analyst_transport.",
        }
    )

    success_envelope = AnalysisReviewPacketEnvelope.model_validate(
        {
            "status": "success",
            "review_packet": success.model_dump(mode="json"),
        }
    )
    failure_envelope = AnalysisReviewPacketEnvelope.model_validate(
        {
            "status": "failed",
            "review_packet": failure.model_dump(mode="json"),
        }
    )

    assert success_envelope.status == "success"
    assert failure_envelope.status == "failed"


def test_review_packet_model_rejects_invalid_failure_stage() -> None:
    with pytest.raises(ValidationError):
        AnalysisFailureReviewPacket.model_validate(
            {
                "packet_kind": "analysis_failure",
                "status": "failed",
                "theme_id": "theme_review_failure",
                "failure_stage": "unknown_stage",
                "run_flags": ["analysis_dry_run"],
                "summary_text": "deterministic failure summary",
                "runtime_summary": "deterministic runtime summary",
                "error_message": "deterministic failure message",
            }
        )


def test_review_packet_envelope_requires_matching_status() -> None:
    success = AnalysisSuccessReviewPacket.model_validate(
        {
            "packet_kind": "analysis_success",
            "status": "success",
            "theme_id": "theme_review_success",
            "run_flags": ["analysis_dry_run", "policy_computed"],
            "summary_text": "deterministic success summary",
            "runtime_summary": "deterministic runtime summary",
            "candidate_posture": "candidate",
            "reasoning_posture": "candidate",
            "policy_decision": "allow",
            "decision_score": 0.801,
            "readiness_score": 0.731,
            "risk_penalty": 0.221,
        }
    )

    with pytest.raises(ValidationError):
        AnalysisReviewPacketEnvelope.model_validate(
            {
                "status": "failed",
                "review_packet": success.model_dump(mode="json"),
            }
        )
