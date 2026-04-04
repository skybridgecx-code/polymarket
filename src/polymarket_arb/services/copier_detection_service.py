from __future__ import annotations

from typing import Any

from polymarket_arb.config import Settings
from polymarket_arb.relationships.engine import RelationshipEngine
from polymarket_arb.services.wallet_backfill_service import WalletBackfillService


class CopierDetectionService:
    def __init__(
        self,
        settings: Settings,
        *,
        wallet_backfill_service: WalletBackfillService | None = None,
    ) -> None:
        self._settings = settings
        self._wallet_backfill_service = wallet_backfill_service or WalletBackfillService(settings)

    async def build_relationship_reports(self, *, limit: int) -> list[dict[str, Any]]:
        _, _, wallet_activities = await self._wallet_backfill_service.collect_wallet_backfill(
            limit=limit
        )
        reports = RelationshipEngine().build_relationship_reports(activities=wallet_activities)
        return [report.to_output() for report in reports]
