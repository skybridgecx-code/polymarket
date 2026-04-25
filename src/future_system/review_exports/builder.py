"""Deterministic export payload builder for review bundles."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.execution_boundary_contract.cryp_confirmation_export import (
    ReviewedPolymarketExternalConfirmationSignal,
)
from future_system.review_bundles.models import (
    AnalysisFailureReviewBundle,
    AnalysisReviewBundleEnvelope,
    AnalysisSuccessReviewBundle,
)
from future_system.review_exports.models import (
    AnalysisFailureReviewExportPayload,
    AnalysisReviewExportPackage,
    AnalysisSuccessReviewExportPayload,
)
from future_system.review_packets.models import (
    AnalysisFailureReviewPacket,
    AnalysisSuccessReviewPacket,
)

_SUPPORTED_CRYP_SIGNAL_ASSETS = ("BTC", "ETH", "SOL", "XRP")
_COMPARISON_DIRECTION_SIGNAL_MAP: dict[str, Literal["buy", "sell", "veto"]] = {
    "bullish": "buy",
    "bearish": "sell",
    "mixed": "veto",
    "unknown": "veto",
}


def build_review_export_payloads(
    *,
    review_bundle: AnalysisReviewBundleEnvelope,
) -> AnalysisReviewExportPackage:
    """Build deterministic JSON-ready and markdown export payloads from one review bundle."""

    bundle = review_bundle.review_bundle
    if isinstance(bundle, AnalysisSuccessReviewBundle):
        packet = bundle.review_packet.review_packet
        if not isinstance(packet, AnalysisSuccessReviewPacket):
            raise ValueError("review_export_success_packet_mismatch")

        success_payload = AnalysisSuccessReviewExportPayload(
            export_kind="analysis_success_export",
            status="success",
            theme_id=bundle.theme_id,
            bundle_kind=bundle.bundle_kind,
            packet_kind=packet.packet_kind,
            run_flags=list(bundle.run_flags),
            json_payload=_success_json_payload(bundle=bundle, packet=packet),
            markdown_document=_success_markdown_document(bundle),
            export_summary=_success_export_summary(
                theme_id=bundle.theme_id,
                run_flags=bundle.run_flags,
            ),
        )
        return AnalysisReviewExportPackage(
            theme_id=success_payload.theme_id,
            status=success_payload.status,
            export_kind=success_payload.export_kind,
            run_flags=list(success_payload.run_flags),
            payload=success_payload,
            cryp_external_confirmation_signal=_success_cryp_signal_payload(
                bundle=bundle,
            ),
        )

    if not isinstance(bundle, AnalysisFailureReviewBundle):
        raise ValueError("review_export_failure_bundle_mismatch")

    failure_packet = bundle.review_packet.review_packet
    if not isinstance(failure_packet, AnalysisFailureReviewPacket):
        raise ValueError("review_export_failure_packet_mismatch")

    failure_payload = AnalysisFailureReviewExportPayload(
        export_kind="analysis_failure_export",
        status="failed",
        theme_id=bundle.theme_id,
        bundle_kind=bundle.bundle_kind,
        packet_kind=failure_packet.packet_kind,
        failure_stage=bundle.failure_stage,
        run_flags=list(bundle.run_flags),
        json_payload=_failure_json_payload(bundle=bundle, packet=failure_packet),
        markdown_document=_failure_markdown_document(bundle),
        export_summary=_failure_export_summary(
            theme_id=bundle.theme_id,
            failure_stage=bundle.failure_stage,
            run_flags=bundle.run_flags,
        ),
    )
    return AnalysisReviewExportPackage(
        theme_id=failure_payload.theme_id,
        status=failure_payload.status,
        export_kind=failure_payload.export_kind,
        run_flags=list(failure_payload.run_flags),
        payload=failure_payload,
    )


def _success_cryp_signal_payload(
    *,
    bundle: AnalysisSuccessReviewBundle,
) -> dict[str, object] | None:
    success = bundle.runtime_result.success
    if success is None:
        raise ValueError("review_export_success_runtime_payload_missing")

    context_bundle = success.context_bundle
    asset = _supported_cryp_asset(context_bundle)
    if asset is None:
        return None

    comparison_direction = context_bundle.comparison.polymarket_summary.direction
    signal = _signal_for_policy_decision(
        comparison_direction=comparison_direction,
        policy_decision=success.policy_decision.decision,
    )
    if signal is None:
        return None

    reviewed_signal = ReviewedPolymarketExternalConfirmationSignal(
        asset=asset,
        signal=signal,
        confidence_adjustment=_confidence_adjustment_for_signal(
            signal=signal,
            candidate_confidence=context_bundle.candidate.confidence_score,
        ),
        rationale=_cryp_signal_rationale(
            asset=asset,
            comparison_direction=comparison_direction,
            policy_decision=success.policy_decision.decision,
        ),
        source_system="polymarket-arb",
        supporting_tags=_cryp_signal_supporting_tags(
            context_bundle=context_bundle,
            comparison_direction=comparison_direction,
            policy_decision=success.policy_decision.decision,
        ),
        correlation_id=f"{success.theme_id}.analysis_success_export",
    )
    return reviewed_signal.model_dump(mode="json", exclude_none=True)


def _supported_cryp_asset(context_bundle: OpportunityContextBundle) -> str | None:
    symbol_candidates: list[str | None] = [
        context_bundle.candidate.primary_symbol,
        context_bundle.crypto_evidence.primary_symbol,
    ]
    symbol_candidates.extend(
        proxy.symbol for proxy in context_bundle.crypto_evidence.proxy_evidence if proxy.is_primary
    )
    symbol_candidates.extend(
        asset.symbol
        for asset in context_bundle.theme_link.matched_assets
        if asset.role == "primary_proxy"
    )
    symbol_candidates.extend(context_bundle.crypto_evidence.matched_symbols)

    for symbol in symbol_candidates:
        supported_asset = _normalize_supported_cryp_asset(symbol)
        if supported_asset is not None:
            return supported_asset
    return None


def _normalize_supported_cryp_asset(symbol: str | None) -> str | None:
    if symbol is None:
        return None

    normalized = symbol.strip().upper()
    if not normalized:
        return None

    for asset in _SUPPORTED_CRYP_SIGNAL_ASSETS:
        if normalized == asset:
            return asset
        if normalized.startswith(f"{asset}-"):
            return asset
        if normalized in {f"{asset}USD", f"{asset}USDT"}:
            return asset
    return None


def _confidence_adjustment_for_signal(
    *,
    signal: Literal["buy", "sell", "veto"],
    candidate_confidence: float,
) -> float:
    if signal == "veto":
        return 0.0
    return round(min(0.2, max(0.0, (candidate_confidence - 0.5) / 3.0)), 3)


def _signal_for_policy_decision(
    *,
    comparison_direction: str,
    policy_decision: str,
) -> Literal["buy", "sell", "veto"] | None:
    if policy_decision != "allow":
        return "veto"
    return _COMPARISON_DIRECTION_SIGNAL_MAP.get(comparison_direction)


def _cryp_signal_rationale(
    *,
    asset: str,
    comparison_direction: str,
    policy_decision: str,
) -> str:
    return (
        "Structured Polymarket review signal from "
        "comparison.polymarket_summary.direction="
        f"{comparison_direction}; asset={asset}; policy_decision={policy_decision}."
    )


def _cryp_signal_supporting_tags(
    *,
    context_bundle: OpportunityContextBundle,
    comparison_direction: str,
    policy_decision: str,
) -> list[str]:
    return [
        "polymarket",
        "reviewed",
        "bridge_export",
        "direction_source:comparison.polymarket_summary.direction",
        f"comparison_direction:{comparison_direction}",
        f"comparison_alignment:{context_bundle.comparison.alignment}",
        f"candidate_posture:{context_bundle.candidate.posture}",
        f"policy_decision:{policy_decision}",
    ]


def _success_json_payload(
    *,
    bundle: AnalysisSuccessReviewBundle,
    packet: AnalysisSuccessReviewPacket,
) -> dict[str, object]:
    return {
        "theme_id": bundle.theme_id,
        "status": bundle.status,
        "bundle_kind": bundle.bundle_kind,
        "packet_kind": packet.packet_kind,
        "run_flags": list(bundle.run_flags),
        "bundle_summary": bundle.bundle_summary,
        "review_summary": packet.summary_text,
        "runtime_summary": packet.runtime_summary,
        "policy_decision": packet.policy_decision,
        "reasoning_posture": packet.reasoning_posture,
        "rendered_text": bundle.rendered_text,
        "rendered_markdown": bundle.rendered_markdown,
    }


def _failure_json_payload(
    *,
    bundle: AnalysisFailureReviewBundle,
    packet: AnalysisFailureReviewPacket,
) -> dict[str, object]:
    return {
        "theme_id": bundle.theme_id,
        "status": bundle.status,
        "bundle_kind": bundle.bundle_kind,
        "packet_kind": packet.packet_kind,
        "failure_stage": bundle.failure_stage,
        "run_flags": list(bundle.run_flags),
        "bundle_summary": bundle.bundle_summary,
        "review_summary": packet.summary_text,
        "runtime_summary": packet.runtime_summary,
        "error_message": packet.error_message,
        "rendered_text": bundle.rendered_text,
        "rendered_markdown": bundle.rendered_markdown,
    }


def _success_markdown_document(bundle: AnalysisSuccessReviewBundle) -> str:
    run_flags = _run_flags_text(bundle.run_flags)
    return (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_success_export`\n"
        "- Status: `success`\n"
        f"- Theme ID: `{bundle.theme_id}`\n"
        f"- Bundle Kind: `{bundle.bundle_kind}`\n"
        "- Packet Kind: `analysis_success`\n"
        f"- Run Flags: `{run_flags}`\n"
        f"- Bundle Summary: {bundle.bundle_summary}\n"
        "## Rendered Review\n"
        f"{bundle.rendered_markdown}"
    )


def _failure_markdown_document(bundle: AnalysisFailureReviewBundle) -> str:
    run_flags = _run_flags_text(bundle.run_flags)
    return (
        "# Analysis Review Export\n"
        "- Export Kind: `analysis_failure_export`\n"
        "- Status: `failed`\n"
        f"- Theme ID: `{bundle.theme_id}`\n"
        f"- Bundle Kind: `{bundle.bundle_kind}`\n"
        "- Packet Kind: `analysis_failure`\n"
        f"- Failure Stage: `{bundle.failure_stage}`\n"
        f"- Run Flags: `{run_flags}`\n"
        f"- Bundle Summary: {bundle.bundle_summary}\n"
        "## Rendered Review\n"
        f"{bundle.rendered_markdown}"
    )


def _success_export_summary(*, theme_id: str, run_flags: Sequence[str]) -> str:
    flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "export_kind=analysis_success_export; "
        "status=success; "
        f"run_flags={flags_text}."
    )


def _failure_export_summary(
    *,
    theme_id: str,
    failure_stage: str,
    run_flags: Sequence[str],
) -> str:
    flags_text = _run_flags_text(run_flags)
    return (
        f"theme_id={theme_id}; "
        "export_kind=analysis_failure_export; "
        "status=failed; "
        f"failure_stage={failure_stage}; "
        f"run_flags={flags_text}."
    )


def _run_flags_text(run_flags: Sequence[str]) -> str:
    if not run_flags:
        return "none"
    return ",".join(run_flags)
