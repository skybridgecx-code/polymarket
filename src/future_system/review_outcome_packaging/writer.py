from __future__ import annotations

import json
from pathlib import Path

from future_system.review_outcome_packaging.builder import (
    build_review_outcome_package,
    render_review_outcome_handoff_markdown,
)
from future_system.review_outcome_packaging.models import ReviewOutcomePackage


def write_review_outcome_package(
    *,
    run_id: str,
    markdown_artifact_path: Path,
    json_artifact_path: Path,
    operator_review_metadata_path: Path,
    target_root: Path,
) -> ReviewOutcomePackage:
    package = build_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_artifact_path,
        json_artifact_path=json_artifact_path,
        operator_review_metadata_path=operator_review_metadata_path,
        target_root=target_root,
    )

    package_dir = Path(package.paths.package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    Path(package.paths.handoff_summary_path).write_text(
        render_review_outcome_handoff_markdown(package=package),
        encoding="utf-8",
    )
    Path(package.paths.handoff_payload_path).write_text(
        json.dumps(package.payload.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return package
