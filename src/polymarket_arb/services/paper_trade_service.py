from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polymarket_arb.config import Settings
from polymarket_arb.execution import ExecutionPlanBuilder, PaperTradeSimulator
from polymarket_arb.models.execution import PaperTradeResult
from polymarket_arb.models.opportunity import OpportunityCandidate
from polymarket_arb.services.scan_service import ScanService


class PaperTradeService:
    def __init__(
        self,
        settings: Settings,
        *,
        scan_service: ScanService | None = None,
    ) -> None:
        self._settings = settings
        self._scan_service = scan_service or ScanService(settings)
        self._plan_builder = ExecutionPlanBuilder(settings)
        self._simulator = PaperTradeSimulator(settings)

    async def build_paper_trade_rows(
        self,
        *,
        limit: int,
        fixture_path: str | None = None,
    ) -> list[dict[str, Any]]:
        opportunities = await self._load_opportunities(limit=limit, fixture_path=fixture_path)
        reports = self.build_reports_from_opportunities(opportunities=opportunities)
        return [report.to_output() for report in reports]

    def build_reports_from_opportunities(
        self,
        *,
        opportunities: list[OpportunityCandidate],
    ) -> list[PaperTradeResult]:
        reports: list[PaperTradeResult] = []
        for opportunity in opportunities:
            plan = self._plan_builder.build_plan(opportunity=opportunity)
            reports.append(self._simulator.simulate(plan=plan))
        return reports

    async def _load_opportunities(
        self,
        *,
        limit: int,
        fixture_path: str | None,
    ) -> list[OpportunityCandidate]:
        if fixture_path is not None:
            payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                raw_rows = payload.get("opportunities", [])
            else:
                raw_rows = payload
        else:
            raw_rows = await self._scan_service.build_scan_rows(limit=limit)

        if not isinstance(raw_rows, list):
            raise TypeError(
                "Paper-trade input must be a JSON list or an object with opportunities."
            )

        opportunities = [
            OpportunityCandidate.model_validate(item)
            for item in raw_rows[:limit]
            if isinstance(item, dict)
        ]
        return opportunities
