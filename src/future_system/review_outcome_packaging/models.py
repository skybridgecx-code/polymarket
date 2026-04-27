from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ReviewOutcomePackagePaths(BaseModel):
    package_dir: str
    handoff_summary_path: str
    handoff_payload_path: str


class ReviewOutcomePackagePayload(BaseModel):
    package_version: Literal["v1"] = "v1"
    local_only: bool = True
    run_id: str
    run_status: str
    export_kind: str
    markdown_artifact_path: str
    json_artifact_path: str
    operator_review_metadata_path: str
    review_status: str
    operator_decision: str | None = None
    review_notes_summary: str | None = None
    reviewer_identity: str | None = None
    cryp_external_confirmation_signal: dict[str, object] | None = None
    package_marker: str = Field(
        default="deterministic_local_review_outcome_package",
    )


class ReviewOutcomePackage(BaseModel):
    payload: ReviewOutcomePackagePayload
    paths: ReviewOutcomePackagePaths


def package_dir_for_run(*, target_root: Path, run_id: str) -> Path:
    return target_root / f"{run_id}.package"
