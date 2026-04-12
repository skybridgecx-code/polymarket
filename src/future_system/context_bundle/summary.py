"""Deterministic operator summary helpers for opportunity context bundles."""

from __future__ import annotations

from collections.abc import Sequence

from future_system.context_bundle.models import OpportunityContextBundle


def build_operator_summary(
    *,
    theme_id: str,
    candidate_posture: str,
    comparison_alignment: str,
    completeness_score: float,
    freshness_score: float,
    confidence_score: float,
    conflict_score: float,
    flags: Sequence[str],
) -> str:
    """Build a compact deterministic operator summary string from bundle signals."""

    top_flags = list(flags[:3])
    flags_text = "none" if not top_flags else ",".join(top_flags)
    return (
        f"theme_id={theme_id}; "
        f"posture={candidate_posture}; "
        f"alignment={comparison_alignment}; "
        f"completeness={completeness_score:.3f}; "
        f"freshness={freshness_score:.3f}; "
        f"confidence={confidence_score:.3f}; "
        f"conflict={conflict_score:.3f}; "
        f"flags={flags_text}."
    )


def summarize_opportunity_context_bundle(bundle: OpportunityContextBundle) -> str:
    """Produce a deterministic compact summary for one opportunity context bundle."""

    return build_operator_summary(
        theme_id=bundle.theme_id,
        candidate_posture=bundle.candidate.posture,
        comparison_alignment=bundle.comparison.alignment,
        completeness_score=bundle.quality.completeness_score,
        freshness_score=bundle.quality.freshness_score,
        confidence_score=bundle.quality.confidence_score,
        conflict_score=bundle.quality.conflict_score,
        flags=bundle.flags,
    )
