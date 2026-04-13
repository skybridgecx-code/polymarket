"""Route-flow helpers for the operator UI review artifacts surface."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast
from urllib.parse import quote

from fastapi import Response
from fastapi.responses import HTMLResponse, RedirectResponse

from .artifact_reads import ArtifactRunDetail, ArtifactRunHistory
from .render_templates import (
    render_detail_page,
    render_error_page,
    render_list_page,
)
from .root_status import (
    ArtifactsRootStatus,
    artifacts_root_unavailable_message,
)


class TriggerRunResultLike(Protocol):
    """Minimal trigger-run result shape needed by route handlers."""

    run_id: str
    target_subdirectory: str


TriggerReviewArtifactRunFn = Callable[..., object]
ReadReviewArtifactRunDetailFn = Callable[..., ArtifactRunDetail]
ResolveTargetSubdirectoryFn = Callable[..., tuple[Path, str]]
DiscoverReviewArtifactHistoryFn = Callable[..., ArtifactRunHistory]


def handle_list_runs_request(
    *,
    root_status: ArtifactsRootStatus,
    discover_review_artifact_history_fn: DiscoverReviewArtifactHistoryFn,
    trigger_error: str | None,
    last_context_source: str,
    last_analyst_mode: str,
    last_target_subdirectory: str,
    trigger_analyst_mode_choices: tuple[str, ...],
) -> str:
    """Build one list-page response body from current root status and history."""

    history = discover_history_for_root_status(
        root_status=root_status,
        discover_review_artifact_history_fn=discover_review_artifact_history_fn,
    )
    return render_list_page(
        history=history,
        root_status=root_status,
        trigger_error=trigger_error,
        last_context_source=last_context_source,
        last_analyst_mode=last_analyst_mode,
        last_target_subdirectory=last_target_subdirectory,
        trigger_analyst_mode_choices=trigger_analyst_mode_choices,
    )


def handle_trigger_run_request(
    *,
    root_status: ArtifactsRootStatus,
    context_source: str,
    analyst_mode: str,
    target_subdirectory: str,
    trigger_analyst_mode_choices: tuple[str, ...],
    trigger_review_artifact_run_fn: TriggerReviewArtifactRunFn,
    discover_review_artifact_history_fn: DiscoverReviewArtifactHistoryFn,
) -> Response:
    """Handle one trigger request while preserving existing bounded UI behavior."""

    if not root_status.is_usable or root_status.resolved_root is None:
        return HTMLResponse(
            content=handle_list_runs_request(
                root_status=root_status,
                discover_review_artifact_history_fn=discover_review_artifact_history_fn,
                trigger_error=(
                    "artifacts_root_unavailable: "
                    f"{artifacts_root_unavailable_message(root_status=root_status)}"
                ),
                last_context_source=context_source,
                last_analyst_mode=analyst_mode,
                last_target_subdirectory=target_subdirectory,
                trigger_analyst_mode_choices=trigger_analyst_mode_choices,
            ),
            status_code=422,
        )

    try:
        run_result_obj = trigger_review_artifact_run_fn(
            artifacts_root=root_status.resolved_root,
            context_source=context_source,
            analyst_mode=analyst_mode,
            target_subdirectory=target_subdirectory,
        )
        run_result = cast(TriggerRunResultLike, run_result_obj)
    except ValueError as exc:
        return HTMLResponse(
            content=handle_list_runs_request(
                root_status=root_status,
                discover_review_artifact_history_fn=discover_review_artifact_history_fn,
                trigger_error=f"Invalid trigger input: {exc}",
                last_context_source=context_source,
                last_analyst_mode=analyst_mode,
                last_target_subdirectory=target_subdirectory,
                trigger_analyst_mode_choices=trigger_analyst_mode_choices,
            ),
            status_code=422,
        )

    encoded_subdirectory = quote(run_result.target_subdirectory, safe="")
    return RedirectResponse(
        url=f"/runs/{run_result.run_id}?created=1&target_subdirectory={encoded_subdirectory}",
        status_code=303,
    )


def handle_view_run_request(
    *,
    root_status: ArtifactsRootStatus,
    run_id: str,
    created: int | None,
    target_subdirectory: str | None,
    read_review_artifact_run_detail_fn: ReadReviewArtifactRunDetailFn,
    resolve_target_subdirectory_fn: ResolveTargetSubdirectoryFn,
) -> Response:
    """Handle one run-detail read request while preserving existing UI behavior."""

    if not root_status.is_usable or root_status.resolved_root is None:
        return HTMLResponse(
            content=render_error_page(
                title="Run Read Error",
                message=(
                    "artifacts_root_unavailable: "
                    f"{artifacts_root_unavailable_message(root_status=root_status)}"
                ),
                back_href="/",
                back_label="Back to runs",
            ),
            status_code=422,
        )

    detail_root = root_status.resolved_root
    normalized_target_subdirectory: str | None = None
    if target_subdirectory is not None:
        try:
            detail_root, normalized_target_subdirectory = resolve_target_subdirectory_fn(
                artifacts_root=root_status.resolved_root,
                target_subdirectory=target_subdirectory,
                create=False,
            )
        except ValueError as exc:
            if created == 1:
                return HTMLResponse(
                    content=render_error_page(
                        title="Trigger Result Unavailable",
                        message=build_trigger_result_unavailable_message(
                            run_id=run_id,
                            target_subdirectory=target_subdirectory,
                            detail_error=str(exc),
                        ),
                        back_href="/",
                        back_label="Back to runs",
                    ),
                    status_code=422,
                )
            return HTMLResponse(
                content=render_error_page(
                    title="Run Read Error",
                    message=str(exc),
                    back_href="/",
                    back_label="Back to runs",
                ),
                status_code=422,
            )

    try:
        detail = read_review_artifact_run_detail_fn(
            artifacts_root=detail_root,
            run_id=run_id,
        )
    except ValueError as exc:
        if created == 1:
            return HTMLResponse(
                content=render_error_page(
                    title="Trigger Result Unavailable",
                    message=build_trigger_result_unavailable_message(
                        run_id=run_id,
                        target_subdirectory=normalized_target_subdirectory,
                        detail_error=str(exc),
                    ),
                    back_href="/",
                    back_label="Back to runs",
                ),
                status_code=422,
            )
        status_code = 404 if str(exc).startswith("artifact_run_not_found") else 422
        return HTMLResponse(
            content=render_error_page(
                title="Run Read Error",
                message=str(exc),
                back_href="/",
                back_label="Back to runs",
            ),
            status_code=status_code,
        )

    return HTMLResponse(
        content=render_detail_page(
            detail=detail,
            created_via_trigger=(created == 1),
            target_subdirectory=normalized_target_subdirectory,
        )
    )


def discover_history_for_root_status(
    *,
    root_status: ArtifactsRootStatus,
    discover_review_artifact_history_fn: DiscoverReviewArtifactHistoryFn,
) -> ArtifactRunHistory:
    """Return history for usable roots, else deterministic empty history."""

    if not root_status.is_usable or root_status.resolved_root is None:
        return ArtifactRunHistory(runs=[], issues=[])
    return discover_review_artifact_history_fn(artifacts_root=root_status.resolved_root)


def build_trigger_result_unavailable_message(
    *,
    run_id: str,
    target_subdirectory: str | None,
    detail_error: str,
) -> str:
    """Render one deterministic error message for created-but-unreadable runs."""

    target_context = target_subdirectory if target_subdirectory is not None else "(not provided)"
    return (
        "trigger_result_unavailable: newly triggered run is missing or partially readable. "
        f"run_id={run_id}; target_subdirectory={target_context}; detail_error={detail_error}"
    )


__all__ = [
    "build_trigger_result_unavailable_message",
    "discover_history_for_root_status",
    "handle_list_runs_request",
    "handle_trigger_run_request",
    "handle_view_run_request",
]
