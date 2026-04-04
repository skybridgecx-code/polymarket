from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"

    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


class RelationshipEvidenceItem(BaseModel):
    event_slug: str | None
    condition_id: str
    token_id: str
    side: str
    leader_activity_id: str
    follower_activity_id: str
    leader_activity_at: str
    follower_activity_at: str
    lag_seconds: int
    leader_source_reference: str
    follower_source_reference: str

    def to_output(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RelationshipReport(BaseModel):
    leader_wallet: str
    follower_wallet: str
    relationship_type: Literal["same_leg_same_side_lag"]
    matched_events_count: int
    matched_legs_count: int
    lag_summary_seconds: dict[str, int | None]
    confidence_score: Decimal | None
    status: Literal["accepted", "rejected"]
    rejection_reason: str | None
    explanation: str
    evidence: list[RelationshipEvidenceItem]

    def to_output(self) -> dict[str, Any]:
        return {
            "leader_wallet": self.leader_wallet,
            "follower_wallet": self.follower_wallet,
            "relationship_type": self.relationship_type,
            "matched_events_count": self.matched_events_count,
            "matched_legs_count": self.matched_legs_count,
            "lag_summary_seconds": self.lag_summary_seconds,
            "confidence_score": _decimal_to_string(self.confidence_score),
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "explanation": self.explanation,
            "evidence": [item.to_output() for item in self.evidence],
        }
