from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel

PacketType = Literal["opportunities", "relationships", "paper_trade"]


class ReviewPacket(BaseModel):
    packet_id: str
    packet_type: PacketType
    created_at: str | None
    source_references: list[str]
    summarized_findings: dict[str, Any]
    raw_result_references: list[str]
    embedded_records: list[dict[str, Any]]
    status: Literal["ready", "warning"]
    notes: list[str]

    def to_output(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ReplayEvaluation(BaseModel):
    evaluation_id: str
    subject_type: PacketType
    compared_records_count: int
    matches_count: int
    mismatches_count: int
    drift_reasons: list[str]
    status: Literal["pass", "fail"]
    explanation: str

    def to_output(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)
