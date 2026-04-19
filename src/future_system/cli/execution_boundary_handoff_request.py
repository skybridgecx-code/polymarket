"""CLI wrapper for deterministic local execution-boundary handoff-request building."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from future_system.execution_boundary_contract import (
    write_execution_boundary_handoff_request_from_package,
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    package_dir = Path(args.package_dir)
    output_path = Path(args.output_path) if args.output_path else None

    try:
        handoff_request_path = write_execution_boundary_handoff_request_from_package(
            package_dir=package_dir,
            output_path=output_path,
        )
    except ValueError as exc:
        print(f"execution_boundary_handoff_request_cli_error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "result_kind": "execution_boundary_handoff_request_build_result",
        "status": "built",
        "package_dir": str(package_dir),
        "handoff_request_path": str(handoff_request_path),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.execution_boundary_handoff_request",
        description=(
            "Build one deterministic execution-boundary handoff_request.json "
            "from a local review outcome package directory."
        ),
    )
    parser.add_argument(
        "--package-dir",
        required=True,
        help="Path to one <run_id>.package directory containing handoff_payload.json.",
    )
    parser.add_argument(
        "--output-path",
        required=False,
        help=(
            "Optional output path for handoff_request.json. Defaults to "
            "<package_dir>/handoff_request.json."
        ),
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
