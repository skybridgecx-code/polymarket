"""CLI wrapper for exporting reviewed Polymarket signals into cryp advisory JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from future_system.execution_boundary_contract.cryp_confirmation_export import (
    write_cryp_external_confirmation_artifact_from_package,
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        result = write_cryp_external_confirmation_artifact_from_package(
            package_dir=Path(args.package_dir),
            output_path=Path(args.output_path),
        )
    except ValueError as exc:
        print(f"cryp_external_confirmation_export_cli_error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m future_system.cli.cryp_external_confirmation_export",
        description=(
            "Export a reviewed Polymarket package into the exact cryp "
            "external_confirmation_advisory_v1 JSON artifact shape."
        ),
    )
    parser.add_argument(
        "--package-dir",
        required=True,
        help="Path to one reviewed <run_id>.package directory containing handoff_payload.json.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Destination path for the cryp-consumable external confirmation JSON artifact.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
