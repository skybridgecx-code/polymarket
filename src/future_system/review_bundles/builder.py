"""Deterministic builder for composing runtime, packet, and rendered review outputs."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.review_bundles.models import (
    AnalysisFailureReviewBundle,
    AnalysisReviewBundleEnvelope,
    AnalysisSuccessReviewBundle,
)
from future_system.review_packets.builder import build_analysis_review_packet
from future_system.review_renderers.renderer import (
    render_review_packet_markdown,
    render_review_packet_text,
)
from future_system.runtime.models import AnalysisRunResultEnvelope


def build_review_bundle(
    *,
    runtime_result: AnalysisRunResultEnvelope,
) -> AnalysisReviewBundleEnvelope:
    """Compose a deterministic review bundle from one runtime result envelope."""

    review_packet = build_analysis_review_packet(runtime_result=runtime_result)
    rendered_text = render_review_packet_text(review_packet=review_packet)
    rendered_markdown = render_review_packet_markdown(review_packet=review_packet)

    if runtime_result.status == "success":
        success = runtime_result.success
        assert success is not None

        success_bundle = AnalysisSuccessReviewBundle(
            bundle_kind="analysis_success_bundle",
            status="success",
            theme_id=success.theme_id,
            runtime_result=runtime_result,
            review_packet=review_packet,
            rendered_text=rendered_text,
            rendered_markdown=rendered_markdown,
            run_flags=list(success.run_flags),
            bundle_summary=_build_success_bundle_summary(
                theme_id=success.theme_id,
                run_flags=success.run_flags,
            ),
        )
        return AnalysisReviewBundleEnvelope(status="success", review_bundle=success_bundle)

    failure = runtime_result.failure
    assert failure is not None

    failure_bundle = AnalysisFailureReviewBundle(
        bundle_kind="analysis_failure_bundle",
        status="failed",
        theme_id=failure.theme_id,
        failure_stage=failure.failure_stage,
        runtime_result=runtime_result,
        review_packet=review_packet,
        rendered_text=rendered_text,
        rendered_markdown=rendered_markdown,
        run_flags=list(failure.run_flags),
        bundle_summary=_build_failure_bundle_summary(
            theme_id=failure.theme_id,
            failure_stage=failure.failure_stage,
            run_flags=failure.run_flags,
        ),
    )
    return AnalysisReviewBundleEnvelope(status="failed", review_bundle=failure_bundle)


def _build_success_bundle_summary(*, theme_id: str, run_flags: Sequence[str]) -> str:
    flags_text = "none" if not run_flags else ",".join(run_flags[:4])
    return (
        f"theme_id={theme_id}; "
        "bundle_kind=analysis_success_bundle; "
        "status=success; "
        f"run_flags={flags_text}."
    )


def _build_failure_bundle_summary(
    *,
    theme_id: str,
    failure_stage: str,
    run_flags: Sequence[str],
) -> str:
    flags_text = "none" if not run_flags else ",".join(run_flags[:4])
    return (
        f"theme_id={theme_id}; "
        "bundle_kind=analysis_failure_bundle; "
        "status=failed; "
        f"failure_stage={failure_stage}; "
        f"run_flags={flags_text}."
    )
