"""Deterministic plain-text and markdown renderers for analysis review packets."""

from __future__ import annotations

from typing import Literal

from future_system.review_packets.models import (
    AnalysisReviewPacketEnvelope,
    AnalysisSuccessReviewPacket,
)

RenderFormat = Literal["text", "markdown"]


def render_review_packet(
    *,
    review_packet: AnalysisReviewPacketEnvelope,
    output_format: RenderFormat = "text",
) -> str:
    """Render one analysis review packet envelope into deterministic operator-facing text."""

    if output_format == "text":
        return render_review_packet_text(review_packet=review_packet)
    if output_format == "markdown":
        return render_review_packet_markdown(review_packet=review_packet)
    raise ValueError("output_format must be either 'text' or 'markdown'.")


def render_review_packet_text(*, review_packet: AnalysisReviewPacketEnvelope) -> str:
    """Render deterministic plain text for one analysis review packet envelope."""

    packet = review_packet.review_packet
    if isinstance(packet, AnalysisSuccessReviewPacket):
        run_flags = _run_flags_text(packet.run_flags)
        return (
            "analysis_review_packet\n"
            "packet_kind=analysis_success\n"
            "status=success\n"
            f"theme_id={packet.theme_id}\n"
            f"candidate_posture={packet.candidate_posture}\n"
            f"reasoning_posture={packet.reasoning_posture}\n"
            f"policy_decision={packet.policy_decision}\n"
            f"decision_score={packet.decision_score:.3f}\n"
            f"readiness_score={packet.readiness_score:.3f}\n"
            f"risk_penalty={packet.risk_penalty:.3f}\n"
            f"run_flags={run_flags}\n"
            f"summary_text={packet.summary_text}\n"
            f"runtime_summary={packet.runtime_summary}"
        )

    failure_packet = packet
    run_flags = _run_flags_text(failure_packet.run_flags)
    return (
        "analysis_review_packet\n"
        "packet_kind=analysis_failure\n"
        "status=failed\n"
        f"theme_id={failure_packet.theme_id}\n"
        f"failure_stage={failure_packet.failure_stage}\n"
        f"run_flags={run_flags}\n"
        f"summary_text={failure_packet.summary_text}\n"
        f"runtime_summary={failure_packet.runtime_summary}\n"
        f"error_message={failure_packet.error_message}"
    )


def render_review_packet_markdown(*, review_packet: AnalysisReviewPacketEnvelope) -> str:
    """Render deterministic markdown for one analysis review packet envelope."""

    packet = review_packet.review_packet
    if isinstance(packet, AnalysisSuccessReviewPacket):
        run_flags = _run_flags_text(packet.run_flags)
        return (
            "## Analysis Review Packet\n"
            "- Packet Kind: `analysis_success`\n"
            "- Status: `success`\n"
            f"- Theme ID: `{packet.theme_id}`\n"
            f"- Candidate Posture: `{packet.candidate_posture}`\n"
            f"- Reasoning Posture: `{packet.reasoning_posture}`\n"
            f"- Policy Decision: `{packet.policy_decision}`\n"
            f"- Decision Score: `{packet.decision_score:.3f}`\n"
            f"- Readiness Score: `{packet.readiness_score:.3f}`\n"
            f"- Risk Penalty: `{packet.risk_penalty:.3f}`\n"
            f"- Run Flags: `{run_flags}`\n"
            f"- Summary: {packet.summary_text}\n"
            f"- Runtime Summary: {packet.runtime_summary}"
        )

    failure_packet = packet
    run_flags = _run_flags_text(failure_packet.run_flags)
    return (
        "## Analysis Review Packet\n"
        "- Packet Kind: `analysis_failure`\n"
        "- Status: `failed`\n"
        f"- Theme ID: `{failure_packet.theme_id}`\n"
        f"- Failure Stage: `{failure_packet.failure_stage}`\n"
        f"- Run Flags: `{run_flags}`\n"
        f"- Summary: {failure_packet.summary_text}\n"
        f"- Runtime Summary: {failure_packet.runtime_summary}\n"
        f"- Error Message: {failure_packet.error_message}"
    )


def _run_flags_text(run_flags: list[str]) -> str:
    if not run_flags:
        return "none"
    return ",".join(run_flags)
