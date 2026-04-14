"""Deterministic surface tests for future_system.review_artifacts composition flow."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.live_analyst.adapter import LiveAnalystAdapter
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.operator_review_models import OperatorReviewDecisionRecord
from future_system.review_artifacts.flow import build_and_write_review_artifacts
from future_system.review_artifacts.operator_review_metadata import (
    write_initialized_operator_review_metadata_companion,
)
from future_system.runtime.models import AnalysisRunFailureStage
from future_system.runtime.runner import run_analysis_pipeline_result
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_RUNTIME_FIXTURE_PATH = Path("tests/fixtures/future_system/runtime/runtime_inputs.json")


def test_build_and_write_review_artifacts_success_wires_bundle_export_and_file_write(
    tmp_path: Path,
) -> None:
    runtime_result = _success_runtime_result()

    flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
    )
    flow_result = flow.flow_result

    assert flow.status == "success"
    assert flow_result.flow_kind == "analysis_success_artifact_flow"
    assert flow_result.status == "success"
    assert flow_result.theme_id == "theme_ctx_strong"
    assert flow_result.target_directory == str(tmp_path.resolve())
    assert flow_result.run_flags == [
        "analysis_dry_run",
        "stub_analyst_used",
        "reasoning_parsed",
        "policy_computed",
    ]
    assert flow_result.review_bundle.status == "success"
    assert flow_result.export_package.status == "success"
    assert flow_result.file_write_result.status == "success"

    markdown_path = Path(flow_result.file_write_result.markdown_file_path)
    json_path = Path(flow_result.file_write_result.json_file_path)
    assert (
        markdown_path.read_text(encoding="utf-8")
        == flow_result.export_package.payload.markdown_document
    )
    assert json.loads(json_path.read_text(encoding="utf-8")) == (
        flow_result.export_package.model_dump(mode="json")
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_run_flags"),
    [
        ("analyst_timeout", ["analysis_dry_run", "analyst_timeout"]),
        ("analyst_transport", ["analysis_dry_run", "analyst_transport_failed"]),
        ("reasoning_parse", ["analysis_dry_run", "reasoning_parse_failed"]),
    ],
)
def test_build_and_write_review_artifacts_failure_preserves_stage_identity(
    tmp_path: Path,
    failure_stage: AnalysisRunFailureStage,
    expected_run_flags: list[str],
) -> None:
    runtime_result = _failure_runtime_result(failure_stage)

    flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
    )
    flow_result = flow.flow_result

    assert flow.status == "failed"
    assert flow_result.flow_kind == "analysis_failure_artifact_flow"
    assert flow_result.status == "failed"
    assert flow_result.theme_id == "theme_ctx_strong"
    assert flow_result.target_directory == str(tmp_path.resolve())
    assert flow_result.failure_stage == failure_stage
    assert flow_result.run_flags == expected_run_flags
    assert flow_result.review_bundle.status == "failed"
    assert flow_result.export_package.status == "failed"
    assert flow_result.file_write_result.status == "failed"
    assert flow_result.file_write_result.failure_stage == failure_stage

    markdown_path = Path(flow_result.file_write_result.markdown_file_path)
    json_path = Path(flow_result.file_write_result.json_file_path)

    markdown_text = markdown_path.read_text(encoding="utf-8")
    json_document = json.loads(json_path.read_text(encoding="utf-8"))

    assert f"- Failure Stage: `{failure_stage}`" in markdown_text
    assert json_document["payload"]["failure_stage"] == failure_stage
    assert "policy_decision" not in json_document["payload"]["json_payload"]


def test_build_and_write_review_artifacts_is_deterministic_for_same_runtime_result(
    tmp_path: Path,
) -> None:
    runtime_result = _success_runtime_result()

    flow_a = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
    )
    flow_b = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
    )

    assert flow_a.model_dump(mode="json") == flow_b.model_dump(mode="json")

    markdown_path = Path(flow_a.flow_result.file_write_result.markdown_file_path)
    json_path = Path(flow_a.flow_result.file_write_result.json_file_path)
    assert markdown_path.read_text(encoding="utf-8") == Path(
        flow_b.flow_result.file_write_result.markdown_file_path
    ).read_text(encoding="utf-8")
    assert json_path.read_text(encoding="utf-8") == Path(
        flow_b.flow_result.file_write_result.json_file_path
    ).read_text(encoding="utf-8")


def test_build_and_write_review_artifacts_default_does_not_write_operator_review_metadata(
    tmp_path: Path,
) -> None:
    runtime_result = _success_runtime_result()

    flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
    )
    run_id = Path(flow.flow_result.file_write_result.json_file_path).stem

    assert not (tmp_path / f"{run_id}.operator_review.json").exists()


def test_build_and_write_review_artifacts_opt_in_writes_pending_operator_review_metadata(
    tmp_path: Path,
) -> None:
    runtime_result = _success_runtime_result()

    flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
        initialize_operator_review=True,
    )
    run_id = Path(flow.flow_result.file_write_result.json_file_path).stem
    metadata_path = tmp_path / f"{run_id}.operator_review.json"

    assert metadata_path.exists()

    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )
    assert record.review_status == "pending"
    assert record.operator_decision is None
    assert record.artifact.run_id == run_id
    assert record.artifact.status == "success"
    assert record.artifact.failure_stage is None
    assert record.artifact.json_file_path == flow.flow_result.file_write_result.json_file_path
    assert (
        record.artifact.markdown_file_path
        == flow.flow_result.file_write_result.markdown_file_path
    )


def test_build_and_write_review_artifacts_opt_in_preserves_failure_stage_in_metadata(
    tmp_path: Path,
) -> None:
    runtime_result = _failure_runtime_result("reasoning_parse")

    flow = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
        initialize_operator_review=True,
    )
    run_id = Path(flow.flow_result.file_write_result.json_file_path).stem
    metadata_path = tmp_path / f"{run_id}.operator_review.json"
    record = OperatorReviewDecisionRecord.model_validate(
        json.loads(metadata_path.read_text(encoding="utf-8"))
    )

    assert record.review_status == "pending"
    assert record.artifact.status == "failed"
    assert record.artifact.export_kind == "analysis_failure_export"
    assert record.artifact.failure_stage == "reasoning_parse"


def test_build_and_write_review_artifacts_opt_in_does_not_overwrite_existing_metadata(
    tmp_path: Path,
) -> None:
    runtime_result = _success_runtime_result()

    first = build_and_write_review_artifacts(
        runtime_result=runtime_result,
        target_directory=tmp_path,
        initialize_operator_review=True,
    )
    run_id = Path(first.flow_result.file_write_result.json_file_path).stem
    metadata_path = tmp_path / f"{run_id}.operator_review.json"
    existing = metadata_path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite"):
        build_and_write_review_artifacts(
            runtime_result=runtime_result,
            target_directory=tmp_path,
            initialize_operator_review=True,
        )

    assert metadata_path.read_text(encoding="utf-8") == existing


def test_write_initialized_operator_review_metadata_companion_bounds_writes_to_target_directory(
    tmp_path: Path,
) -> None:
    outside_path = tmp_path.parent / "outside.operator_review.json"

    with pytest.raises(ValueError, match="run_id contains invalid characters"):
        write_initialized_operator_review_metadata_companion(
            target_directory=tmp_path,
            run_id="../outside",
            artifact_payload={
                "theme_id": "theme_ctx_strong",
                "status": "success",
                "export_kind": "analysis_success_export",
            },
        )

    assert not outside_path.exists()


def _success_runtime_result() -> Any:
    return run_analysis_pipeline_result(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
    )


def _failure_runtime_result(failure_stage: AnalysisRunFailureStage) -> Any:
    context_bundle = _bundle("strong_complete")
    if failure_stage == "analyst_timeout":
        analyst: Any = LiveAnalystAdapter(
            transport=_TimeoutTransport(),
            timeout_seconds=0.1,
        )
    elif failure_stage == "analyst_transport":
        analyst = LiveAnalystAdapter(
            transport=_StaticTransport(response={"choices": []}),
            timeout_seconds=1.0,
        )
    else:
        malformed_case = _runtime_case("malformed_analyst_output")
        analyst = _MalformedAnalyst(payload=malformed_case["malformed_payload"])

    return run_analysis_pipeline_result(
        context_bundle=context_bundle,
        analyst=analyst,
    )


class _MalformedAnalyst:
    is_stub = False

    def __init__(self, *, payload: str) -> None:
        self._payload = payload

    def analyze(self, **_: object) -> str:
        return self._payload


class _StaticTransport:
    def __init__(self, *, response: Mapping[str, Any] | str) -> None:
        self._response = response

    def request(self, *, request: object) -> Mapping[str, Any] | str:
        del request
        return self._response


class _TimeoutTransport:
    def request(self, *, request: object) -> Mapping[str, Any] | str:
        del request
        raise TimeoutError("simulated timeout")


def _runtime_case(case_name: str) -> dict[str, Any]:
    payload = json.loads(_RUNTIME_FIXTURE_PATH.read_text(encoding="utf-8"))
    for item in payload:
        if item["case"] == case_name:
            return dict(item)
    raise AssertionError(f"Missing runtime fixture case: {case_name}")


def _bundle(case_name: str) -> Any:
    case = _context_cases()[case_name]
    return build_opportunity_context_bundle(
        theme_link_packet=case["theme_link"],
        polymarket_evidence_packet=case["polymarket_evidence"],
        divergence_packet=case["divergence"],
        crypto_evidence_packet=case["crypto_evidence"],
        comparison_packet=case["comparison"],
        news_evidence_packet=case["news_evidence"],
        candidate_packet=case["candidate"],
    )


def _context_cases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_CONTEXT_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        entry["case"]: {
            "theme_link": ThemeLinkPacket.model_validate(entry["theme_link"]),
            "polymarket_evidence": ThemeEvidencePacket.model_validate(entry["polymarket_evidence"]),
            "divergence": ThemeDivergencePacket.model_validate(entry["divergence"]),
            "crypto_evidence": ThemeCryptoEvidencePacket.model_validate(entry["crypto_evidence"]),
            "comparison": ThemeComparisonPacket.model_validate(entry["comparison"]),
            "news_evidence": ThemeNewsEvidencePacket.model_validate(entry["news_evidence"]),
            "candidate": CandidateSignalPacket.model_validate(entry["candidate"]),
        }
        for entry in payload
    }
