"""CLI wrapper for deterministic dispatch into cryp local transport inbound tree."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from future_system.execution_boundary_contract import dispatch_execution_boundary_handoff_request


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        result = dispatch_execution_boundary_handoff_request(
            run_id=args.run_id,
            artifacts_root=Path(args.artifacts_root),
            cryp_transport_root=Path(args.cryp_transport_root),
            attempt_id=args.attempt_id,
            dry_run=bool(args.dry_run),
        )
    except ValueError as exc:
        print(f"execution_boundary_dispatch_cli_error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.execution_boundary_dispatch",
        description=(
            "Build package + handoff request + validation, then dispatch "
            "the validated handoff_request.json to cryp canonical inbound transport path."
        ),
    )
    parser.add_argument("--run-id", required=True, help="Reviewed run id to package and dispatch.")
    parser.add_argument(
        "--artifacts-root",
        required=True,
        help=(
            "Directory containing <run_id>.md, <run_id>.json, and "
            "<run_id>.operator_review.json."
        ),
    )
    parser.add_argument(
        "--cryp-transport-root",
        required=True,
        help=(
            "Canonical cryp transport root containing inbound/, pickup/, "
            "responses/, archive/ trees."
        ),
    )
    parser.add_argument(
        "--attempt-id",
        required=False,
        help=(
            "Optional attempt id. If omitted, a deterministic epoch-ns attempt id is generated."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Validate and print resolved canonical paths only; do not write into cryp inbound tree."
        ),
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
