"""Config and dependency assembly helpers for the operator UI review artifacts app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from future_system.operator_ui.root_status import ArtifactsRootStatus, resolve_artifacts_root_status
from future_system.operator_ui.route_handlers import (
    DiscoverReviewArtifactHistoryFn,
    ReadReviewArtifactRunDetailFn,
    ResolveTargetSubdirectoryFn,
    TriggerReviewArtifactRunFn,
)

DEFAULT_TRIGGER_ANALYST_MODE_CHOICES: tuple[str, ...] = (
    "stub",
    "analyst_timeout",
    "analyst_transport",
    "reasoning_parse",
)
DEFAULT_TRIGGER_ANALYST_MODE = "stub"
DEFAULT_TRIGGER_TARGET_SUBDIRECTORY = "operator_runs"
DEFAULT_TRIGGER_CONTEXT_SOURCE = ""


@dataclass(frozen=True)
class ReviewArtifactsOperatorUIConfig:
    """Deterministic operator UI defaults for trigger/list handlers."""

    trigger_analyst_mode_choices: tuple[str, ...]
    default_trigger_analyst_mode: str
    default_trigger_context_source: str
    default_target_subdirectory: str


@dataclass(frozen=True)
class ReviewArtifactsOperatorUIDependencies:
    """Bounded route dependency callables for operator UI handlers."""

    discover_review_artifact_history_fn: DiscoverReviewArtifactHistoryFn
    trigger_review_artifact_run_fn: TriggerReviewArtifactRunFn
    read_review_artifact_run_detail_fn: ReadReviewArtifactRunDetailFn
    resolve_target_subdirectory_fn: ResolveTargetSubdirectoryFn


@dataclass(frozen=True)
class ReviewArtifactsOperatorUIAssembly:
    """Assembled root status, defaults, and route dependencies for app factory wiring."""

    root_status: ArtifactsRootStatus
    config: ReviewArtifactsOperatorUIConfig
    dependencies: ReviewArtifactsOperatorUIDependencies


def build_review_artifacts_operator_ui_config() -> ReviewArtifactsOperatorUIConfig:
    """Build deterministic defaults used by trigger/list handlers."""

    return ReviewArtifactsOperatorUIConfig(
        trigger_analyst_mode_choices=DEFAULT_TRIGGER_ANALYST_MODE_CHOICES,
        default_trigger_analyst_mode=DEFAULT_TRIGGER_ANALYST_MODE,
        default_trigger_context_source=DEFAULT_TRIGGER_CONTEXT_SOURCE,
        default_target_subdirectory=DEFAULT_TRIGGER_TARGET_SUBDIRECTORY,
    )


def build_review_artifacts_operator_ui_assembly(
    *,
    artifacts_root: str | Path | None,
    discover_review_artifact_history_fn: DiscoverReviewArtifactHistoryFn,
    trigger_review_artifact_run_fn: TriggerReviewArtifactRunFn,
    read_review_artifact_run_detail_fn: ReadReviewArtifactRunDetailFn,
    resolve_target_subdirectory_fn: ResolveTargetSubdirectoryFn,
) -> ReviewArtifactsOperatorUIAssembly:
    """Assemble deterministic root status, defaults, and route dependencies."""

    config = build_review_artifacts_operator_ui_config()
    root_status = resolve_artifacts_root_status(artifacts_root)
    dependencies = ReviewArtifactsOperatorUIDependencies(
        discover_review_artifact_history_fn=discover_review_artifact_history_fn,
        trigger_review_artifact_run_fn=trigger_review_artifact_run_fn,
        read_review_artifact_run_detail_fn=read_review_artifact_run_detail_fn,
        resolve_target_subdirectory_fn=resolve_target_subdirectory_fn,
    )
    return ReviewArtifactsOperatorUIAssembly(
        root_status=root_status,
        config=config,
        dependencies=dependencies,
    )


__all__ = [
    "DEFAULT_TRIGGER_ANALYST_MODE_CHOICES",
    "DEFAULT_TRIGGER_TARGET_SUBDIRECTORY",
    "ReviewArtifactsOperatorUIAssembly",
    "ReviewArtifactsOperatorUIConfig",
    "ReviewArtifactsOperatorUIDependencies",
    "build_review_artifacts_operator_ui_assembly",
    "build_review_artifacts_operator_ui_config",
]
