"""CLI entrypoint for writing a bounded local review outcome package for one reviewed run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from future_system.review_outcome_packaging import write_review_outcome_package


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    artifacts_root = Path(args.artifacts_root)
    run_id = args.run_id.strip()
    target_root = Path(args.target_root) if args.target_root else artifacts_root

    markdown_artifact_path = artifacts_root / f"{run_id}.md"
    json_artifact_path = artifacts_root / f"{run_id}.json"
    operator_review_metadata_path = artifacts_root / f"{run_id}.operator_review.json"

    try:
        package = write_review_outcome_package(
            run_id=run_id,
            markdown_artifact_path=markdown_artifact_path,
            json_artifact_path=json_artifact_path,
            operator_review_metadata_path=operator_review_metadata_path,
            target_root=target_root,
        )
    except ValueError as exc:
        print(f"review_outcome_package_cli_error: {exc}", file=sys.stderr)
        return 2

    print(f"run_id: {package.payload.run_id}")
    print(f"package_dir: {package.paths.package_dir}")
    print(f"handoff_summary_path: {package.paths.handoff_summary_path}")
    print(f"handoff_payload_path: {package.paths.handoff_payload_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.review_outcome_package",
        description="Write a bounded local review outcome package for one reviewed run.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Reviewed run id to package.",
    )
    parser.add_argument(
        "--artifacts-root",
        required=True,
        help=(
            "Directory containing <run_id>.md, <run_id>.json, and "
            "<run_id>.operator_review.json."
        ),
    )
    parser.add_argument(
        "--target-root",
        required=False,
        help=(
            "Optional output root for the generated package directory. "
            "Defaults to artifacts root."
        ),
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
