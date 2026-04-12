"""Deterministic builders that convert runtime result envelopes into review packets."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.review_packets.models import (
    AnalysisFailureReviewPacket,
    AnalysisReviewPacketEnvelope,
    AnalysisSuccessReviewPacket,
)
from future_system.runtime.models import AnalysisRunResultEnvelope


def build_analysis_review_packet(
    *,
    runtime_result: AnalysisRunResultEnvelope,
) -> AnalysisReviewPacketEnvelope:
    """Convert one runtime result envelope into a deterministic review packet envelope."""

    if runtime_result.status == "success":
        success = runtime_result.success
        assert success is not None

        success_review_packet = AnalysisSuccessReviewPacket(
            packet_kind="analysis_success",
            status="success",
            theme_id=success.theme_id,
            run_flags=list(success.run_flags),
            summary_text=_build_success_summary(
                theme_id=success.theme_id,
                candidate_posture=success.context_bundle.candidate.posture,
                reasoning_posture=success.reasoning_output.recommended_posture,
                policy_decision=success.policy_decision.decision,
                run_flags=success.run_flags,
            ),
            runtime_summary=success.run_summary,
            candidate_posture=success.context_bundle.candidate.posture,
            reasoning_posture=success.reasoning_output.recommended_posture,
            policy_decision=success.policy_decision.decision,
            decision_score=success.policy_decision.decision_score,
            readiness_score=success.policy_decision.readiness_score,
            risk_penalty=success.policy_decision.risk_penalty,
        )
        return AnalysisReviewPacketEnvelope(status="success", review_packet=success_review_packet)

    failure = runtime_result.failure
    assert failure is not None

    failure_review_packet = AnalysisFailureReviewPacket(
        packet_kind="analysis_failure",
        status="failed",
        theme_id=failure.theme_id,
        failure_stage=failure.failure_stage,
        run_flags=list(failure.run_flags),
        summary_text=_build_failure_summary(
            theme_id=failure.theme_id,
            failure_stage=failure.failure_stage,
            run_flags=failure.run_flags,
        ),
        runtime_summary=failure.run_summary,
        error_message=failure.error_message,
    )
    return AnalysisReviewPacketEnvelope(status="failed", review_packet=failure_review_packet)


def _build_success_summary(
    *,
    theme_id: str,
    candidate_posture: str,
    reasoning_posture: str,
    policy_decision: str,
    run_flags: Sequence[str],
) -> str:
    flags_text = "none" if not run_flags else ",".join(run_flags[:4])
    return (
        f"theme_id={theme_id}; "
        "packet_kind=analysis_success; "
        "status=success; "
        f"candidate_posture={candidate_posture}; "
        f"reasoning_posture={reasoning_posture}; "
        f"policy_decision={policy_decision}; "
        f"run_flags={flags_text}."
    )


def _build_failure_summary(
    *,
    theme_id: str,
    failure_stage: str,
    run_flags: Sequence[str],
) -> str:
    flags_text = "none" if not run_flags else ",".join(run_flags[:4])
    return (
        f"theme_id={theme_id}; "
        "packet_kind=analysis_failure; "
        "status=failed; "
        f"failure_stage={failure_stage}; "
        f"run_flags={flags_text}."
    )
