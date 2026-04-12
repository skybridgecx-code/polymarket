"""Deterministic export payload builder for review bundles."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.review_bundles.models import (
    AnalysisFailureReviewBundle,
    AnalysisReviewBundleEnvelope,
    AnalysisSuccessReviewBundle,
)
from future_system.review_exports.models import (
    AnalysisFailureReviewExportPayload,
    AnalysisReviewExportPackage,
    AnalysisSuccessReviewExportPayload,
)
from future_system.review_packets.models import (
    AnalysisFailureReviewPacket,
    AnalysisSuccessReviewPacket,
)


def build_review_export_payloads(
    *,
    review_bundle: AnalysisReviewBundleEnvelope,
) -> AnalysisReviewExportPackage:
    """Build deterministic JSON-ready and markdown export payloads from one review bundle."""

    bundle = review_bundle.review_bundle
    if isinstance(bundle, AnalysisSuccessReviewBundle):
        packet = bundle.review_packet.review_packet
        if not isinstance(packet, AnalysisSuccessReviewPacket):
            raise ValueError("review_export_success_packet_mismatch")

        success_payload = AnalysisSuccessReviewExportPayload(
            export_kind="analysis_success_export",
            status="success",
            theme_id=bundle.theme_id,
            bundle_kind=bundle.bundle_kind,
            packet_kind=packet.packet_kind,
            run_flags=list(bundle.run_flags),
            json_payload=_success_json_payload(bundle=bundle, packet=packet),
            markdown_document=_success_markdown_document(bundle),
            export_summary=_success_export_summary(
                theme_id=bundle.theme_id,
                run_flags=bundle.run_flags,
            ),
        )
        return AnalysisReviewExportPackage(
            theme_id=success_payload.theme_id,
            status=success_payload.status,
            export_kind=success_payload.export_kind,
            run_flags=list(success_payload.run_flags),
            payload=success_payload,
        )

    if not isinstance(bundle, AnalysisFailureReviewBundle):
        raise ValueError("review_export_failure_bundle_mismatch")

    failure_packet = bundle.review_packet.review_packet
    if not isinstance(failure_packet, AnalysisFailureReviewPacket):
        raise ValueError("review_export_failure_packet_mismatch")

    failure_payload = AnalysisFailureReviewExportPayload(
        export_kind="analysis_failure_export",
        status="failed",
        theme_id=bundle.theme_id,
        bundle_kind=bundle.bundle_kind,
        packet_kind=failure_packet.packet_kind,
        failure_stage=bundle.failure_stage,
        run_flags=list(bundle.run_flags),
        json_payload=_failure_json_payload(bundle=bundle, packet=failure_packet),
        markdown_document=_failure_markdown_document(bundle),
        export_summary=_failure_export_summary(
            theme_id=bundle.theme_id,
            failure_stage=bundle.failure_stage,
            run_flags=bundle.run_flags,
        ),
    )
    return AnalysisReviewExportPackage(
        theme_id=failure_payload.theme_id,
        status=failure_payload.status,
        export_kind=failure_payload.export_kind,
        run_flags=list(failure_payload.run_flags),
        payload=failure_payload,
    )


def _success_json_payload(
    *,
    bundle: AnalysisSuccessReviewBundle,
    packet: AnalysisSuccessReviewPacket,
) -> dict[str, object]:
    return {
        "theme_id": bundle.theme_id,
        "status": bundle.status,
        "bundle_kind": bundle.bundle_kind,
        "packet_kind": packet.packet_kind,
        "run_flags": list(bundle.run_flags),
        "bundle_summary": bundle.bundle_summary,
        "review_summary": packet.summary_text,
        "runtime_summary": packet.runtime_summary,
        "policy_decision": packet.policy_decision,
        "reasoning_posture": packet.reasoning_posture,
        "rendered_text": bundle.rendered_text,
        "rendered_markdown": bundle.rendered_markdown,
    }


def _failure_json_payload(
    *,
    bundle: AnalysisFailureReviewBundle,
    packet: AnalysisFailureReviewPacket,
) -> dict[str, object]:
    return {
        "theme_id": bundle.theme_id,
        "status": bundle.status,
        "bundle_kind": bundle.bundle_kind,
        "packet_kind": packet.packet_kind,
        "failure_stage": bundle.failure_stage,
        "run_flags": list(bundle.run_flags),
        "bundle_summary": bundle.bundle_summary,
        "review_summary": packet.summary_text,
        "runtime_summary": packet.runtime_summary,
        "error_message": packet.error_message,
        "rendered_text": bundle.rendered_text,
        "rendered_markdown": bundle.rendered_markdown,
    }


def _success_markdown_document(bundle: AnalysisSuccessReviewBundle) -> str:
    run_flags = _run_flags_text(bundle.run_flags)
    return (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_success_export`\n"
        "- Status: `success`\n"
        f"- Theme ID: `{bundle.theme_id}`\n"
        f"- Bundle Kind: `{bundle.bundle_kind}`\n"
        "- Packet Kind: `analysis_success`\n"
        f"- Run Flags: `{run_flags}`\n"
        f"- Bundle Summary: {bundle.bundle_summary}\n"
        "## Rendered Review\n"
        f"{bundle.rendered_markdown}"
    )


def _failure_markdown_document(bundle: AnalysisFailureReviewBundle) -> str:
    run_flags = _run_flags_text(bundle.run_flags)
    return (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_failure_export`\n"
        "- Status: `failed`\n"
        f"- Theme ID: `{bundle.theme_id}`\n"
        f"- Bundle Kind: `{bundle.bundle_kind}`\n"
        "- Packet Kind: `analysis_failure`\n"
        f"- Failure Stage: `{bundle.failure_stage}`\n"
        f"- Run Flags: `{run_flags}`\n"
        f"- Bundle Summary: {bundle.bundle_summary}\n"
        "## Rendered Review\n"
        f"{bundle.rendered_markdown}"
    )


def _success_export_summary(*, theme_id: str, run_flags: Sequence[str]) -> str:
    flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "export_kind=analysis_success_export; "
        "status=success; "
        f"run_flags={flags_text}."
    )


def _failure_export_summary(
    *,
    theme_id: str,
    failure_stage: str,
    run_flags: Sequence[str],
) -> str:
    flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "export_kind=analysis_failure_export; "
        "status=failed; "
        f"failure_stage={failure_stage}; "
        f"run_flags={flags_text}."
    )


def _run_flags_text(run_flags: Sequence[str]) -> str:
    if not run_flags:
        return "none"
    return ",".join(run_flags)
