"""CLI wrapper for local execution-boundary handoff intake/export processing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from future_system.execution_boundary_contract import (
    process_execution_boundary_handoff_request_artifact,
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    handoff_request_path = Path(args.handoff_request_path)
    export_root = Path(args.export_root)

    try:
        result = process_execution_boundary_handoff_request_artifact(
            handoff_request_path=handoff_request_path,
            export_root=export_root,
            require_local_artifacts=args.require_local_artifacts,
        )
    except ValueError as exc:
        print(f"execution_boundary_intake_cli_error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "result_kind": "execution_boundary_intake_result",
        "status": "accepted" if result.accepted else "rejected",
        **result.model_dump(),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.execution_boundary_intake",
        description=(
            "Validate and process one local execution-boundary handoff request "
            "artifact and write deterministic ack/reject output."
        ),
    )
    parser.add_argument(
        "--handoff-request-path",
        required=True,
        help="Path to one handoff request JSON artifact.",
    )
    parser.add_argument(
        "--export-root",
        required=True,
        help="Directory where deterministic ack/reject artifacts are written.",
    )
    parser.add_argument(
        "--require-local-artifacts",
        action="store_true",
        help=(
            "Require handoff payload artifact paths to exist on disk during validation."
        ),
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
