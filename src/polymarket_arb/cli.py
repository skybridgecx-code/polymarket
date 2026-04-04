from __future__ import annotations

import asyncio
import json
from typing import cast

import typer

from polymarket_arb.config import get_settings
from polymarket_arb.logging import configure_logging
from polymarket_arb.models.review import PacketType
from polymarket_arb.review import ReplayEvaluationService, ReviewPacketService
from polymarket_arb.services.copier_detection_service import CopierDetectionService
from polymarket_arb.services.orchestration_service import RefreshOrchestratorService
from polymarket_arb.services.paper_trade_service import PaperTradeService
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


@app.command("paper-trade")
def paper_trade(
    limit: int = typer.Option(
        5,
        min=1,
        help="Number of opportunities to transform into paper-trade plans.",
    ),
    fixture_path: str | None = typer.Option(
        None,
        help="Optional JSON fixture path for deterministic paper-trade input.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    payload = asyncio.run(
        PaperTradeService(settings).build_paper_trade_rows(
            limit=limit,
            fixture_path=fixture_path,
        )
    )
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("review-packet")
def review_packet(
    packet_type: str = typer.Option(
        ...,
        help="Packet subject type: opportunities, relationships, or paper_trade.",
    ),
    limit: int = typer.Option(
        10,
        min=1,
        help="Number of records to load into the review packet.",
    ),
    fixture_path: str | None = typer.Option(
        None,
        help="Optional JSON fixture path for deterministic packet input.",
    ),
) -> None:
    if packet_type not in {"opportunities", "relationships", "paper_trade"}:
        raise typer.BadParameter(
            "packet_type must be one of: opportunities, relationships, paper_trade"
        )
    normalized_packet_type = cast(PacketType, packet_type)

    settings = get_settings()
    configure_logging(settings.log_level)
    payload = asyncio.run(
        ReviewPacketService(settings).build_packet_output(
            packet_type=normalized_packet_type,
            limit=limit,
            fixture_path=fixture_path,
        )
    )
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("replay-evaluate")
def replay_evaluate(
    baseline_path: str = typer.Option(
        ...,
        help="Baseline review packet JSON path.",
    ),
    candidate_path: str = typer.Option(
        ...,
        help="Candidate review packet JSON path.",
    ),
) -> None:
    configure_logging(get_settings().log_level)
    payload = ReplayEvaluationService().evaluate_packet_paths(
        baseline_path=baseline_path,
        candidate_path=candidate_path,
    )
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
