"""Deterministic in-memory manual gate bundle comparisons."""

from __future__ import annotations

from pydantic import BaseModel

from future_system.manual_gate.bundles import ManualGateBundle
from future_system.manual_gate.packets import ManualGateDisposition
from future_system.observability.correlation import CorrelationId


class ManualGateComparison(BaseModel):
    """Pure in-memory comparison artifact for two manual gate bundles."""

    left_packet_id: str
    right_packet_id: str
    left_correlation_id: CorrelationId
    right_correlation_id: CorrelationId
    left_disposition: ManualGateDisposition
    right_disposition: ManualGateDisposition
    same_packet_id: bool
    same_correlation_id: bool
    disposition_changed: bool
    review_ready_changed: bool
    manual_action_required_changed: bool
    added_reasons: list[str]
    removed_reasons: list[str]
    added_required_follow_up: list[str]
    removed_required_follow_up: list[str]
    bundles_equal: bool


def compare_manual_gate_bundles(
    left: ManualGateBundle,
    right: ManualGateBundle,
) -> ManualGateComparison:
    """Compare two manual gate bundles using bounded deterministic fields only."""

    same_packet_id = left.packet_id == right.packet_id
    same_correlation_id = left.correlation_id.value == right.correlation_id.value
    disposition_changed = left.disposition is not right.disposition
    review_ready_changed = left.review_ready is not right.review_ready
    manual_action_required_changed = (
        left.manual_action_required is not right.manual_action_required
    )

    added_reasons = sorted(set(right.packet.reasons) - set(left.packet.reasons))
    removed_reasons = sorted(set(left.packet.reasons) - set(right.packet.reasons))
    added_required_follow_up = sorted(
        set(right.packet.required_follow_up) - set(left.packet.required_follow_up)
    )
    removed_required_follow_up = sorted(
        set(left.packet.required_follow_up) - set(right.packet.required_follow_up)
    )

    bundles_equal = (
        same_packet_id
        and same_correlation_id
        and not disposition_changed
        and not review_ready_changed
        and not manual_action_required_changed
        and not added_reasons
        and not removed_reasons
        and not added_required_follow_up
        and not removed_required_follow_up
    )

    return ManualGateComparison(
        left_packet_id=left.packet_id,
        right_packet_id=right.packet_id,
        left_correlation_id=left.correlation_id,
        right_correlation_id=right.correlation_id,
        left_disposition=left.disposition,
        right_disposition=right.disposition,
        same_packet_id=same_packet_id,
        same_correlation_id=same_correlation_id,
        disposition_changed=disposition_changed,
        review_ready_changed=review_ready_changed,
        manual_action_required_changed=manual_action_required_changed,
        added_reasons=added_reasons,
        removed_reasons=removed_reasons,
        added_required_follow_up=added_required_follow_up,
        removed_required_follow_up=removed_required_follow_up,
        bundles_equal=bundles_equal,
    )
