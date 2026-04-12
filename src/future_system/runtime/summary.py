"""Deterministic summary helpers for end-to-end dry-run analysis runtime packets."""

from __future__ import annotations

from collections.abc import Sequence


def build_analysis_run_summary(
    *,
    theme_id: str,
    candidate_posture: str,
    reasoning_posture: str,
    policy_decision: str,
    decision_score: float,
    readiness_score: float,
    risk_penalty: float,
    run_flags: Sequence[str],
) -> str:
    """Build compact deterministic runtime summary for operator inspection."""

    flags_text = "none" if not run_flags else ",".join(run_flags[:4])
    return (
        f"theme_id={theme_id}; "
        f"candidate_posture={candidate_posture}; "
        f"reasoning_posture={reasoning_posture}; "
        f"policy_decision={policy_decision}; "
        f"decision_score={decision_score:.3f}; "
        f"readiness_score={readiness_score:.3f}; "
        f"risk_penalty={risk_penalty:.3f}; "
        f"run_flags={flags_text}."
    )
