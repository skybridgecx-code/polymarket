"""Structured event definitions for future critical decision paths.

Typed event records for approval, control, and recovery-relevant state changes.
Pure model layer — no emission, no external references, no runtime state.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from future_system.observability.correlation import CorrelationId, RecordScope


class EventKind(str, Enum):
    """Classifies events on future critical decision paths."""

    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    CONTROL_APPLIED = "control_applied"
    CONTROL_RELEASED = "control_released"
    RECOVERY_INITIATED = "recovery_initiated"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FAILED = "recovery_failed"


class FutureSystemEvent(BaseModel):
    """Structured event record for a future critical decision path.

    Pure model, no emission.  Built for replay-style reconstruction and
    attribution of future-system state transitions.  All fields are required
    so that attribution cannot be silently omitted.
    """

    event_id: str
    correlation_id: CorrelationId
    event_kind: EventKind
    record_scope: RecordScope
    occurred_at: datetime
    description: str
    attributed_to: str
