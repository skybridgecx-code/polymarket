from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from polymarket_arb.config import Settings
from polymarket_arb.models.execution import PaperTradeResult
from polymarket_arb.models.opportunity import OpportunityCandidate
from polymarket_arb.models.relationship import RelationshipReport
from polymarket_arb.models.review import PacketType, ReviewPacket, canonical_json
from polymarket_arb.services.copier_detection_service import CopierDetectionService
from polymarket_arb.services.paper_trade_service import PaperTradeService
from polymarket_arb.services.scan_service import ScanService


class ReviewPacketService:
    def __init__(
        self,
        settings: Settings,
        *,
        scan_service: ScanService | None = None,
        copier_detection_service: CopierDetectionService | None = None,
        paper_trade_service: PaperTradeService | None = None,
    ) -> None:
        self._settings = settings
        self._scan_service = scan_service or ScanService(settings)
        self._copier_detection_service = (
            copier_detection_service or CopierDetectionService(settings)
        )
        self._paper_trade_service = paper_trade_service or PaperTradeService(settings)

    async def build_packet_output(
        self,
        *,
        packet_type: PacketType,
        limit: int,
        fixture_path: str | None = None,
    ) -> dict[str, Any]:
        packet = await self.build_packet(
            packet_type=packet_type,
            limit=limit,
            fixture_path=fixture_path,
        )
        return packet.to_output()

    async def build_packet(
        self,
        *,
        packet_type: PacketType,
        limit: int,
        fixture_path: str | None = None,
    ) -> ReviewPacket:
        records, source_reference = await self._load_records(
            packet_type=packet_type,
            limit=limit,
            fixture_path=fixture_path,
        )
        record_references = [
            self._record_reference(packet_type=packet_type, record=record)
            for record in records
        ]
        created_at = self._created_at(packet_type=packet_type, records=records)

        source_references = [source_reference]
        source_references.extend(
            self._record_source_references(packet_type=packet_type, records=records)
        )
        source_references = sorted(set(source_references))

        notes: list[str] = []
        if created_at is None:
            notes.append("created_at_unavailable")
        if any(record.get("status") == "rejected" for record in records):
            notes.append("contains_rejected_records")
        if not records:
            notes.append("empty_packet")

        status: Literal["ready", "warning"] = "warning" if not records else "ready"
        packet_id = self._packet_id(
            packet_type=packet_type,
            record_references=record_references,
            records=records,
        )
        return ReviewPacket(
            packet_id=packet_id,
            packet_type=packet_type,
            created_at=created_at,
            source_references=source_references,
            summarized_findings=self._summarized_findings(records=records),
            raw_result_references=record_references,
            embedded_records=records,
            status=status,
            notes=notes,
        )

    async def _load_records(
        self,
        *,
        packet_type: PacketType,
        limit: int,
        fixture_path: str | None,
    ) -> tuple[list[dict[str, Any]], str]:
        if fixture_path is not None:
            payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("Review packet fixture must be a JSON object.")
            rows = payload.get(packet_type, [])
            if not isinstance(rows, list):
                raise TypeError(f"Fixture field {packet_type!r} must be a JSON list.")
            source_reference = f"fixture:{fixture_path}#{packet_type}"
        else:
            if packet_type == "opportunities":
                rows = await self._scan_service.build_scan_rows(limit=limit)
            elif packet_type == "relationships":
                rows = await self._copier_detection_service.build_relationship_reports(limit=limit)
            else:
                rows = await self._paper_trade_service.build_paper_trade_rows(limit=limit)
            source_reference = f"service:{packet_type}"

        return self._canonical_records(packet_type=packet_type, rows=rows[:limit]), source_reference

    def _canonical_records(
        self,
        *,
        packet_type: PacketType,
        rows: list[Any],
    ) -> list[dict[str, Any]]:
        if packet_type == "opportunities":
            return [
                OpportunityCandidate.model_validate(row).to_output()
                for row in rows
                if isinstance(row, dict)
            ]
        if packet_type == "relationships":
            return [
                RelationshipReport.model_validate(row).to_output()
                for row in rows
                if isinstance(row, dict)
            ]
        return [
            PaperTradeResult.model_validate(row).to_output()
            for row in rows
            if isinstance(row, dict)
        ]

    def _record_reference(self, *, packet_type: PacketType, record: dict[str, Any]) -> str:
        if packet_type == "opportunities":
            token_ids = "+".join(
                str(leg.get("token_id"))
                for leg in record.get("legs", [])
                if isinstance(leg, dict) and leg.get("token_id") is not None
            ) or "no-legs"
            return f"{record['event_slug']}:{record['opportunity_type']}:{token_ids}"
        if packet_type == "relationships":
            return (
                f"{record['leader_wallet']}:{record['follower_wallet']}:"
                f"{record['relationship_type']}"
            )
        return str(record["plan_id"])

    def _record_source_references(
        self,
        *,
        packet_type: PacketType,
        records: list[dict[str, Any]],
    ) -> list[str]:
        refs: list[str] = []
        if packet_type == "relationships":
            for record in records:
                for evidence in record.get("evidence", []):
                    if isinstance(evidence, dict):
                        refs.extend(
                            [
                                str(evidence["leader_source_reference"]),
                                str(evidence["follower_source_reference"]),
                            ]
                        )
        elif packet_type == "paper_trade":
            refs.extend(str(record["source_opportunity_reference"]) for record in records)
        else:
            refs.extend(
                self._record_reference(packet_type=packet_type, record=record)
                for record in records
            )
        return refs

    def _created_at(self, *, packet_type: PacketType, records: list[dict[str, Any]]) -> str | None:
        if packet_type != "relationships":
            return None

        timestamps: list[str] = []
        for record in records:
            for evidence in record.get("evidence", []):
                if isinstance(evidence, dict):
                    for field in ("leader_activity_at", "follower_activity_at"):
                        value = evidence.get(field)
                        if isinstance(value, str):
                            timestamps.append(value)
        return min(timestamps) if timestamps else None

    def _summarized_findings(self, *, records: list[dict[str, Any]]) -> dict[str, Any]:
        accepted_count = sum(1 for record in records if record.get("status") == "accepted")
        rejected_count = sum(1 for record in records if record.get("status") == "rejected")
        return {
            "total_records": len(records),
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
        }

    def _packet_id(
        self,
        *,
        packet_type: PacketType,
        record_references: list[str],
        records: list[dict[str, Any]],
    ) -> str:
        digest = hashlib.sha256(
            canonical_json(
                {
                    "packet_type": packet_type,
                    "record_references": record_references,
                    "records": records,
                }
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"packet:{packet_type}:{digest}"
