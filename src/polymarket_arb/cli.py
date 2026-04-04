from __future__ import annotations

import asyncio
import json

import typer

from polymarket_arb.config import get_settings
from polymarket_arb.logging import configure_logging
from polymarket_arb.services.scan_service import ScanService

app = typer.Typer(add_completion=False, help="Read-only Polymarket analytics CLI.")


@app.callback()
def entrypoint() -> None:
    """Polymarket analytics CLI."""


@app.command()
def scan(
    limit: int = typer.Option(
        5,
        min=1,
        help="Number of events to include in the scan.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    rows = asyncio.run(ScanService(settings).build_scan_rows(limit=limit))
    typer.echo(json.dumps(rows, indent=2, sort_keys=True))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
