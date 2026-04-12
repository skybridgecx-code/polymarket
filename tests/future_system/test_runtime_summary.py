"""Summary helper tests for deterministic runtime run-summary rendering."""

from __future__ import annotations

from future_system.runtime.summary import build_analysis_run_summary


def test_run_summary_is_deterministic() -> None:
    summary_a = build_analysis_run_summary(
        theme_id="theme_runtime_summary",
        candidate_posture="candidate",
        reasoning_posture="watch",
        policy_decision="hold",
        decision_score=0.512,
        readiness_score=0.604,
        risk_penalty=0.441,
        run_flags=["analysis_dry_run", "stub_analyst_used", "reasoning_parsed", "policy_computed"],
    )
    summary_b = build_analysis_run_summary(
        theme_id="theme_runtime_summary",
        candidate_posture="candidate",
        reasoning_posture="watch",
        policy_decision="hold",
        decision_score=0.512,
        readiness_score=0.604,
        risk_penalty=0.441,
        run_flags=["analysis_dry_run", "stub_analyst_used", "reasoning_parsed", "policy_computed"],
    )

    assert summary_a == summary_b


def test_summary_reflects_theme_reasoning_and_final_decision() -> None:
    summary = build_analysis_run_summary(
        theme_id="theme_runtime_summary",
        candidate_posture="watch",
        reasoning_posture="insufficient",
        policy_decision="deny",
        decision_score=0.210,
        readiness_score=0.320,
        risk_penalty=0.820,
        run_flags=["analysis_dry_run", "reasoning_parsed", "policy_computed"],
    )

    assert "theme_id=theme_runtime_summary" in summary
    assert "reasoning_posture=insufficient" in summary
    assert "policy_decision=deny" in summary


def test_summary_reflects_important_flags_where_applicable() -> None:
    summary = build_analysis_run_summary(
        theme_id="theme_runtime_summary",
        candidate_posture="candidate",
        reasoning_posture="candidate",
        policy_decision="allow",
        decision_score=0.840,
        readiness_score=0.790,
        risk_penalty=0.240,
        run_flags=["analysis_dry_run", "stub_analyst_used", "reasoning_parsed", "policy_computed"],
    )

    assert (
        "run_flags=analysis_dry_run,stub_analyst_used,reasoning_parsed,policy_computed."
        in summary
    )
