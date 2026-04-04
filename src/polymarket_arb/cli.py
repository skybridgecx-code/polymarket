from __future__ import annotations

import asyncio
import json

import typer

from polymarket_arb.config import get_settings
from polymarket_arb.logging import configure_logging
from polymarket_arb.services.copier_detection_service import CopierDetectionService
from polymarket_arb.services.orchestration_service import RefreshOrchestratorService
from polymarket_arb.services.scan_service import ScanService
from polymarket_arb.services.wallet_backfill_service import WalletBackfillService

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


@app.command("wallet-backfill")
def wallet_backfill(
    limit: int = typer.Option(
        10,
        min=1,
        help="Number of wallet seeds to discover and backfill.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    payload = asyncio.run(WalletBackfillService(settings).build_wallet_backfill(limit=limit))
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("detect-copiers")
def detect_copiers(
    limit: int = typer.Option(
        10,
        min=1,
        help="Number of wallets to backfill before pair scoring.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    payload = asyncio.run(CopierDetectionService(settings).build_relationship_reports(limit=limit))
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("orchestrate-refresh")
def orchestrate_refresh(
    scan_limit: int = typer.Option(
        5,
        min=1,
        help="Number of events to refresh for opportunity scanning.",
    ),
    relationship_limit: int = typer.Option(
        10,
        min=1,
        help="Number of wallets to backfill before refreshing relationships.",
    ),
    max_websocket_messages: int = typer.Option(
        1,
        min=0,
        help="Maximum number of websocket market messages to consume in this bounded run.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    payload = asyncio.run(
        RefreshOrchestratorService(settings).run_refresh_cycle(
            scan_limit=scan_limit,
            relationship_limit=relationship_limit,
            max_websocket_messages=max_websocket_messages,
        )
    )
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
