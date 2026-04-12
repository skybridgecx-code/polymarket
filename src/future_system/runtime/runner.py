"""Deterministic end-to-end dry-run runtime runner across reasoning and policy layers."""

from __future__ import annotations

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.live_analyst.errors import LiveAnalystTimeoutError, LiveAnalystTransportError
from future_system.policy_engine.engine import evaluate_policy_decision
from future_system.reasoning_contracts.builder import build_reasoning_input_packet
from future_system.reasoning_contracts.models import ReasoningParseError
from future_system.reasoning_contracts.parser import parse_reasoning_output
from future_system.reasoning_contracts.renderer import render_reasoning_prompt_packet
from future_system.runtime.models import AnalysisRunError, AnalysisRunPacket
from future_system.runtime.protocol import AnalystProtocol
from future_system.runtime.summary import build_analysis_run_summary


def run_analysis_pipeline(
    *,
    context_bundle: OpportunityContextBundle,
    analyst: AnalystProtocol,
) -> AnalysisRunPacket:
    """Run deterministic dry-run analysis pipeline from context bundle to policy packet."""

    run_flags: list[str] = ["analysis_dry_run"]
    if getattr(analyst, "is_stub", False):
        run_flags.append("stub_analyst_used")

    reasoning_input = build_reasoning_input_packet(bundle=context_bundle)
    rendered_prompt = render_reasoning_prompt_packet(reasoning_input=reasoning_input)

    try:
        analyst_payload = analyst.analyze(
            reasoning_input=reasoning_input,
            rendered_prompt=rendered_prompt,
        )
    except LiveAnalystTimeoutError as exc:
        failure_flags = [*run_flags, "analyst_timeout"]
        raise AnalysisRunError(
            "analysis_run_failed: "
            f"theme_id={context_bundle.theme_id}; "
            "stage=analyst_timeout; "
            f"flags={','.join(failure_flags)}."
        ) from exc
    except LiveAnalystTransportError as exc:
        failure_flags = [*run_flags, "analyst_transport_failed"]
        raise AnalysisRunError(
            "analysis_run_failed: "
            f"theme_id={context_bundle.theme_id}; "
            "stage=analyst_transport; "
            f"flags={','.join(failure_flags)}."
        ) from exc

    try:
        reasoning_output = parse_reasoning_output(analyst_payload)
    except ReasoningParseError as exc:
        failure_flags = [*run_flags, "reasoning_parse_failed"]
        raise AnalysisRunError(
            "analysis_run_failed: "
            f"theme_id={context_bundle.theme_id}; "
            "stage=reasoning_parse; "
            f"flags={','.join(failure_flags)}."
        ) from exc

    run_flags.append("reasoning_parsed")

    policy_decision = evaluate_policy_decision(
        context_bundle=context_bundle,
        reasoning_output=reasoning_output,
    )
    run_flags.append("policy_computed")

    run_summary = build_analysis_run_summary(
        theme_id=context_bundle.theme_id,
        candidate_posture=context_bundle.candidate.posture,
        reasoning_posture=reasoning_output.recommended_posture,
        policy_decision=policy_decision.decision,
        decision_score=policy_decision.decision_score,
        readiness_score=policy_decision.readiness_score,
        risk_penalty=policy_decision.risk_penalty,
        run_flags=run_flags,
    )

    return AnalysisRunPacket(
        theme_id=context_bundle.theme_id,
        status="success",
        context_bundle=context_bundle,
        reasoning_input=reasoning_input,
        rendered_prompt=rendered_prompt,
        reasoning_output=reasoning_output,
        policy_decision=policy_decision,
        run_flags=run_flags,
        run_summary=run_summary,
    )
