from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from fastapi import FastAPI, Query, Request

from polymarket_arb.api.schemas import (
    HealthResponse,
    OpportunitiesResponse,
    RelationshipsResponse,
    WalletBackfillResponse,
)
from polymarket_arb.config import Settings, get_settings
from polymarket_arb.services.copier_detection_service import CopierDetectionService
from polymarket_arb.services.scan_service import ScanService
from polymarket_arb.services.wallet_backfill_service import WalletBackfillService

ScanServiceFactory = Callable[[Settings], ScanService]
WalletBackfillServiceFactory = Callable[[Settings], WalletBackfillService]
CopierDetectionServiceFactory = Callable[[Settings], CopierDetectionService]


def _default_scan_service_factory(settings: Settings) -> ScanService:
    return ScanService(settings)


def _default_wallet_backfill_service_factory(settings: Settings) -> WalletBackfillService:
    return WalletBackfillService(settings)


def _default_copier_detection_service_factory(settings: Settings) -> CopierDetectionService:
    return CopierDetectionService(settings)


def create_app(
    *,
    scan_service_factory: ScanServiceFactory = _default_scan_service_factory,
    wallet_backfill_service_factory: WalletBackfillServiceFactory = (
        _default_wallet_backfill_service_factory
    ),
    copier_detection_service_factory: CopierDetectionServiceFactory = (
        _default_copier_detection_service_factory
    ),
) -> FastAPI:
    app = FastAPI(title="Polymarket Arb API", version="0.1.0")
    app.state.scan_service_factory = scan_service_factory
    app.state.wallet_backfill_service_factory = wallet_backfill_service_factory
    app.state.copier_detection_service_factory = copier_detection_service_factory

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/opportunities", response_model=OpportunitiesResponse)
    async def opportunities(
        request: Request,
        limit: int = Query(default=5, ge=1),
    ) -> list[dict[str, Any]]:
        service = request.app.state.scan_service_factory(get_settings())
        payload = await service.build_scan_rows(limit=limit)
        return cast(list[dict[str, Any]], payload)

    @app.get("/wallets/backfill", response_model=WalletBackfillResponse)
    async def wallets_backfill(
        request: Request,
        limit: int = Query(default=10, ge=1),
    ) -> dict[str, Any]:
        service = request.app.state.wallet_backfill_service_factory(get_settings())
        payload = await service.build_wallet_backfill(limit=limit)
        return cast(dict[str, Any], payload)

    @app.get("/relationships/copiers", response_model=RelationshipsResponse)
    async def relationships_copiers(
        request: Request,
        limit: int = Query(default=10, ge=1),
    ) -> list[dict[str, Any]]:
        service = request.app.state.copier_detection_service_factory(get_settings())
        payload = await service.build_relationship_reports(limit=limit)
        return cast(list[dict[str, Any]], payload)

    return app


app = create_app()
