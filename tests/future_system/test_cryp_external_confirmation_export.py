from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Literal

import pytest
from future_system.candidates.models import CandidateSignalPacket
from future_system.cli.cryp_external_confirmation_export import main as export_cli_main
from future_system.cli.review_artifacts import main as review_artifacts_cli_main
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.cryp_external_confirmation_signal import (
    map_polymarket_intent_to_reviewed_signal,
    resolve_supported_cryp_confirmation_asset,
)
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.execution_boundary_contract.cryp_confirmation_export import (
    build_cryp_external_confirmation_artifact_from_package,
)
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.review_entrypoints.entry import run_analysis_and_write_review_artifacts
from future_system.review_outcome_packaging import write_review_outcome_package
from future_system.runtime.stub_analyst import DeterministicStubAnalyst
from future_system.theme_graph.models import ThemeLinkPacket

_CRYP_SRC = Path("/Users/muhammadaatif/cryp/src")
_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json"
)
_XRP_BRIDGE_CONTEXT_FIXTURE_PATH = Path(
    "tests/fixtures/future_system/context_bundle/xrp_bridge_context_bundle.json"
)


def test_reviewed_polymarket_signal_maps_to_expected_cryp_asset(tmp_path: Path) -> None:
    package_dir = _write_reviewed_signal_package(
        tmp_path,
        asset="BTC",
        signal="buy",
    )

    artifact = build_cryp_external_confirmation_artifact_from_package(package_dir=package_dir)

    assert artifact.asset == "BTCUSD"
    assert artifact.directional_bias == "buy"
    assert artifact.veto_trade is False
    assert artifact.source_system == "polymarket-arb"
    assert artifact.correlation_id == "theme_btc_regulation.analysis_success_export"


@pytest.mark.parametrize(
    ("asset", "expected_cryp_asset"),
    [
        ("BTC", "BTCUSD"),
        ("ETH", "ETHUSD"),
        ("SOL", "SOLUSD"),
        ("XRP", "XRPUSD"),
    ],
)
def test_generated_review_artifact_maps_supported_assets_to_cryp_json(
    tmp_path: Path,
    capsys,
    asset: str,
    expected_cryp_asset: str,
) -> None:
    target_directory = tmp_path / f"operator_runs_{asset.lower()}"
    target_directory.mkdir()
    entry = run_analysis_and_write_review_artifacts(
        context_bundle=_bundle_for_asset(asset),
        analyst=DeterministicStubAnalyst(),
        target_directory=target_directory,
    )

    flow_result = entry.entry_result.artifact_flow.flow_result
    json_path = Path(flow_result.file_write_result.json_file_path)
    markdown_path = Path(flow_result.file_write_result.markdown_file_path)
    run_id = json_path.stem
    metadata_path = _write_approved_operator_review_metadata(
        target_directory=target_directory,
        run_id=run_id,
        json_path=json_path,
        markdown_path=markdown_path,
        theme_id=f"theme_ctx_{asset.lower()}",
    )

    reviewed_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert reviewed_payload["cryp_external_confirmation_signal"]["asset"] == asset

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=tmp_path / f"packages_{asset.lower()}",
    )
    output_path = tmp_path / "exports" / f"{asset.lower()}_external_confirmation.json"
    exit_code = export_cli_main(
        [
            "--package-dir",
            package.paths.package_dir,
            "--output-path",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    exported_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exported_payload["artifact_kind"] == "external_confirmation_advisory_v1"
    assert exported_payload["asset"] == expected_cryp_asset
    assert exported_payload["directional_bias"] == "buy"
    assert exported_payload["veto_trade"] is False


@pytest.mark.parametrize(
    ("direction", "expected_signal", "expected_bias"),
    [
        ("bullish", "buy", "buy"),
        ("bearish", "sell", "sell"),
    ],
)
def test_xrp_bridge_fixture_reviews_packages_and_exports_cryp_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    direction: Literal["bullish", "bearish"],
    expected_signal: Literal["buy", "sell"],
    expected_bias: Literal["buy", "sell"],
) -> None:
    context_source = _xrp_bridge_context_source(tmp_path=tmp_path, direction=direction)
    context_payload = json.loads(context_source.read_text(encoding="utf-8"))
    assert context_payload["candidate"]["primary_symbol"] == "XRP"
    assert context_payload["comparison"]["polymarket_summary"]["direction"] == direction

    target_directory = tmp_path / f"operator_runs_xrp_{direction}"
    target_directory.mkdir()
    review_exit_code = review_artifacts_cli_main(
        [
            "--context-source",
            str(context_source),
            "--target-directory",
            str(target_directory),
            "--analyst-mode",
            "stub",
        ]
    )
    review_captured = capsys.readouterr()

    assert review_exit_code == 0
    assert review_captured.err == ""
    review_summary = json.loads(review_captured.out)
    json_path = Path(review_summary["json_file_path"])
    markdown_path = Path(review_summary["markdown_file_path"])
    run_id = json_path.stem
    reviewed_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert reviewed_payload["cryp_external_confirmation_signal"]["asset"] == "XRP"
    assert reviewed_payload["cryp_external_confirmation_signal"]["signal"] == expected_signal

    metadata_path = _write_approved_operator_review_metadata(
        target_directory=target_directory,
        run_id=run_id,
        json_path=json_path,
        markdown_path=markdown_path,
        theme_id=review_summary["theme_id"],
    )
    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=tmp_path / f"packages_xrp_{direction}",
    )
    package_dir = Path(package.paths.package_dir)
    handoff_payload = json.loads(
        (package_dir / "handoff_payload.json").read_text(encoding="utf-8")
    )
    assert handoff_payload["cryp_external_confirmation_signal"]["asset"] == "XRP"
    assert handoff_payload["cryp_external_confirmation_signal"]["signal"] == expected_signal

    output_path = tmp_path / "exports" / f"xrp_{direction}_external_confirmation.json"
    export_exit_code = export_cli_main(
        [
            "--package-dir",
            str(package_dir),
            "--output-path",
            str(output_path),
        ]
    )
    export_captured = capsys.readouterr()

    assert export_exit_code == 0
    assert export_captured.err == ""
    exported_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exported_payload["asset"] == "XRPUSD"
    assert exported_payload["directional_bias"] == expected_bias
    assert exported_payload["veto_trade"] is False


def test_buy_sell_and_veto_mapping_is_deterministic(tmp_path: Path) -> None:
    cases: list[
        tuple[
            Literal["buy", "sell", "veto"],
            Literal["buy", "sell", "neutral"],
            bool,
        ]
    ] = [
        ("buy", "buy", False),
        ("sell", "sell", False),
        ("veto", "neutral", True),
    ]

    for signal, expected_bias, expected_veto in cases:
        package_dir = _write_reviewed_signal_package(
            tmp_path / signal,
            asset="ETH",
            signal=signal,
        )

        artifact = build_cryp_external_confirmation_artifact_from_package(package_dir=package_dir)

        assert artifact.asset == "ETHUSD"
        assert artifact.directional_bias == expected_bias
        assert artifact.veto_trade is expected_veto


@pytest.mark.parametrize(
    ("intent", "expected_bias", "expected_veto"),
    [
        ("bullish", "buy", False),
        ("bearish", "sell", False),
        ("neutral", "neutral", True),
        ("veto", "neutral", True),
    ],
)
def test_structured_polymarket_intents_map_to_cryp_bias(
    tmp_path: Path,
    intent: str,
    expected_bias: str,
    expected_veto: bool,
) -> None:
    reviewed_signal = map_polymarket_intent_to_reviewed_signal(intent)
    package_dir = _write_reviewed_signal_package(
        tmp_path / intent,
        asset="XRP",
        signal=reviewed_signal,
    )

    artifact = build_cryp_external_confirmation_artifact_from_package(package_dir=package_dir)

    assert artifact.asset == "XRPUSD"
    assert artifact.directional_bias == expected_bias
    assert artifact.veto_trade is expected_veto


@pytest.mark.parametrize(
    ("asset_symbol", "expected_asset"),
    [
        ("BTC", "BTC"),
        ("ETH-PERP", "ETH"),
        ("SOLUSD", "SOL"),
        ("XRPUSDT", "XRP"),
    ],
)
def test_explicit_structured_asset_source_resolves_supported_assets(
    asset_symbol: str,
    expected_asset: str,
) -> None:
    assert (
        resolve_supported_cryp_confirmation_asset(
            asset_symbol=asset_symbol,
            source_field="candidate.primary_symbol",
        )
        == expected_asset
    )


@pytest.mark.parametrize(
    ("asset_symbol", "expected_error"),
    [
        (None, "missing_cryp_confirmation_asset:candidate.primary_symbol"),
        ("", "missing_cryp_confirmation_asset:candidate.primary_symbol"),
        (
            "DOGE-PERP",
            (
                "unsupported_cryp_confirmation_asset:DOGE-PERP:"
                "source=candidate.primary_symbol:supported=BTC,ETH,SOL,XRP"
            ),
        ),
    ],
)
def test_explicit_structured_asset_source_fails_clearly(
    asset_symbol: str | None,
    expected_error: str,
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        resolve_supported_cryp_confirmation_asset(
            asset_symbol=asset_symbol,
            source_field="candidate.primary_symbol",
        )


def test_exported_json_matches_cryp_consumable_schema(
    tmp_path: Path,
    capsys,
) -> None:
    package_dir = _write_reviewed_signal_package(
        tmp_path,
        asset="SOL",
        signal="sell",
    )
    output_path = tmp_path / "exports" / "sol_external_confirmation.json"

    exit_code = export_cli_main(
        [
            "--package-dir",
            str(package_dir),
            "--output-path",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    summary = json.loads(captured.out)
    assert summary["status"] == "exported"
    assert summary["output_path"] == str(output_path.resolve())

    handoff_payload = json.loads((package_dir / "handoff_payload.json").read_text(encoding="utf-8"))
    assert handoff_payload["cryp_external_confirmation_signal"] == {
        "asset": "SOL",
        "confidence_adjustment": 0.12,
        "correlation_id": "theme_btc_regulation.analysis_success_export",
        "observed_at_epoch_ns": 1700000000000000002,
        "rationale": "Reviewed Polymarket outcome supports the crypto advisory.",
        "signal": "sell",
        "source_system": "polymarket-arb",
        "supporting_tags": ["polymarket", "reviewed", "bridge_export"],
    }

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert set(payload) == {
        "artifact_kind",
        "asset",
        "directional_bias",
        "confidence_adjustment",
        "rationale",
        "source_system",
        "supporting_tags",
        "veto_trade",
        "correlation_id",
        "observed_at_epoch_ns",
    }
    assert payload == {
        "artifact_kind": "external_confirmation_advisory_v1",
        "asset": "SOLUSD",
        "confidence_adjustment": 0.12,
        "correlation_id": "theme_btc_regulation.analysis_success_export",
        "directional_bias": "sell",
        "observed_at_epoch_ns": 1700000000000000002,
        "rationale": "Reviewed Polymarket outcome supports the crypto advisory.",
        "source_system": "polymarket-arb",
        "supporting_tags": ["polymarket", "reviewed", "bridge_export"],
        "veto_trade": False,
    }

    if str(_CRYP_SRC) not in sys.path:
        sys.path.insert(0, str(_CRYP_SRC))
    cryp_models = importlib.import_module("crypto_agent.external_signals.models")
    cryp_artifact = cryp_models.ExternalConfirmationArtifact.model_validate(payload)
    assert cryp_artifact.asset == "SOLUSD"
    assert cryp_artifact.directional_bias == "sell"


def test_generated_review_artifact_packages_and_exports_without_manual_signal_edit(
    tmp_path: Path,
    capsys,
) -> None:
    target_directory = tmp_path / "operator_runs"
    target_directory.mkdir()
    entry = run_analysis_and_write_review_artifacts(
        context_bundle=_bundle("strong_complete"),
        analyst=DeterministicStubAnalyst(),
        target_directory=target_directory,
    )

    flow_result = entry.entry_result.artifact_flow.flow_result
    json_path = Path(flow_result.file_write_result.json_file_path)
    markdown_path = Path(flow_result.file_write_result.markdown_file_path)
    run_id = json_path.stem

    reviewed_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert reviewed_payload["cryp_external_confirmation_signal"]["asset"] == "BTC"

    metadata_path = target_directory / f"{run_id}.operator_review.json"
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": run_id,
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_ctx_strong",
                    "failure_stage": None,
                },
                "review_status": "decided",
                "operator_decision": "approve",
                "review_notes_summary": "Approved generated artifact.",
                "reviewer_identity": "operator_a",
                "run_flags_snapshot": [],
                "decided_at_epoch_ns": 1700000000000000010,
                "updated_at_epoch_ns": 1700000000000000011,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=tmp_path / "packages",
    )
    package_dir = Path(package.paths.package_dir)
    output_path = tmp_path / "exports" / "btc_external_confirmation.json"

    exit_code = export_cli_main(
        [
            "--package-dir",
            str(package_dir),
            "--output-path",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    exported_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exported_payload["asset"] == "BTCUSD"
    assert exported_payload["directional_bias"] == "buy"
    assert exported_payload["confidence_adjustment"] == 0.12
    assert exported_payload["veto_trade"] is False
    assert exported_payload["correlation_id"] == run_id


def test_generated_review_artifact_vetoes_non_allow_policy(
    tmp_path: Path,
) -> None:
    target_directory = tmp_path / "operator_runs"
    target_directory.mkdir()
    entry = run_analysis_and_write_review_artifacts(
        context_bundle=_bundle("conflicted"),
        analyst=DeterministicStubAnalyst(),
        target_directory=target_directory,
    )

    flow_result = entry.entry_result.artifact_flow.flow_result
    json_path = Path(flow_result.file_write_result.json_file_path)
    reviewed_payload = json.loads(json_path.read_text(encoding="utf-8"))
    signal = reviewed_payload["cryp_external_confirmation_signal"]

    assert signal["asset"] == "BTC"
    assert signal["signal"] == "veto"
    assert signal["confidence_adjustment"] == 0.0
    assert "policy_decision:deny" in signal["supporting_tags"]


def _write_reviewed_signal_package(
    tmp_path: Path,
    *,
    asset: str,
    signal: Literal["buy", "sell", "veto"],
) -> Path:
    run_id = "theme_btc_regulation.analysis_success_export"
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    markdown_path = artifacts_root / f"{run_id}.md"
    json_path = artifacts_root / f"{run_id}.json"
    metadata_path = artifacts_root / f"{run_id}.operator_review.json"

    markdown_path.write_text("# reviewed signal\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "entry_kind": "analysis_success_review_entry",
                "cryp_external_confirmation_signal": {
                    "asset": asset,
                    "signal": signal,
                    "confidence_adjustment": 0.12,
                    "rationale": ("Reviewed Polymarket outcome supports the crypto advisory."),
                    "source_system": "polymarket-arb",
                    "supporting_tags": ["polymarket", "reviewed", "bridge_export"],
                    "observed_at_epoch_ns": 1700000000000000002,
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": run_id,
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": "theme_btc_regulation",
                    "failure_stage": None,
                },
                "review_status": "decided",
                "operator_decision": "approve",
                "review_notes_summary": "Approved for cryp advisory export.",
                "reviewer_identity": "operator_a",
                "run_flags_snapshot": [],
                "decided_at_epoch_ns": 1700000000000000000,
                "updated_at_epoch_ns": 1700000000000000001,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    package = write_review_outcome_package(
        run_id=run_id,
        markdown_artifact_path=markdown_path,
        json_artifact_path=json_path,
        operator_review_metadata_path=metadata_path,
        target_root=tmp_path / "packages",
    )
    return Path(package.paths.package_dir)


def _write_approved_operator_review_metadata(
    *,
    target_directory: Path,
    run_id: str,
    json_path: Path,
    markdown_path: Path,
    theme_id: str,
) -> Path:
    metadata_path = target_directory / f"{run_id}.operator_review.json"
    metadata_path.write_text(
        json.dumps(
            {
                "record_kind": "operator_review_decision_record",
                "record_version": 1,
                "artifact": {
                    "run_id": run_id,
                    "status": "success",
                    "export_kind": "analysis_success_export",
                    "json_file_path": str(json_path),
                    "markdown_file_path": str(markdown_path),
                    "theme_id": theme_id,
                    "failure_stage": None,
                },
                "review_status": "decided",
                "operator_decision": "approve",
                "review_notes_summary": "Approved generated artifact.",
                "reviewer_identity": "operator_a",
                "run_flags_snapshot": [],
                "decided_at_epoch_ns": 1700000000000000010,
                "updated_at_epoch_ns": 1700000000000000011,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return metadata_path


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


def _bundle_for_asset(asset: str) -> Any:
    theme_id = f"theme_ctx_{asset.lower()}"
    symbol = f"{asset}-PERP"
    case = _raw_context_case("strong_complete")

    case["theme_link"]["theme_id"] = theme_id
    case["theme_link"]["matched_assets"][0]["symbol"] = asset

    for component in (
        "polymarket_evidence",
        "divergence",
        "crypto_evidence",
        "comparison",
        "news_evidence",
        "candidate",
    ):
        case[component]["theme_id"] = theme_id

    case["crypto_evidence"]["primary_symbol"] = symbol
    case["crypto_evidence"]["matched_symbols"] = [symbol]
    case["crypto_evidence"]["proxy_evidence"][0]["symbol"] = symbol

    case["candidate"]["primary_symbol"] = symbol
    case["candidate"]["title"] = f"{asset} Structured Signal"

    return build_opportunity_context_bundle(
        theme_link_packet=ThemeLinkPacket.model_validate(case["theme_link"]),
        polymarket_evidence_packet=ThemeEvidencePacket.model_validate(case["polymarket_evidence"]),
        divergence_packet=ThemeDivergencePacket.model_validate(case["divergence"]),
        crypto_evidence_packet=ThemeCryptoEvidencePacket.model_validate(case["crypto_evidence"]),
        comparison_packet=ThemeComparisonPacket.model_validate(case["comparison"]),
        news_evidence_packet=ThemeNewsEvidencePacket.model_validate(case["news_evidence"]),
        candidate_packet=CandidateSignalPacket.model_validate(case["candidate"]),
    )


def _xrp_bridge_context_source(
    *,
    tmp_path: Path,
    direction: Literal["bullish", "bearish"],
) -> Path:
    if direction == "bullish":
        return _XRP_BRIDGE_CONTEXT_FIXTURE_PATH

    payload = json.loads(_XRP_BRIDGE_CONTEXT_FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["theme_id"] = "theme_ctx_xrp_bearish"
    payload["title"] = "XRP Bearish Bridge Signal"
    payload["operator_summary"] = payload["operator_summary"].replace(
        "theme_ctx_xrp_bullish",
        "theme_ctx_xrp_bearish",
    )
    for component in (
        "theme_link",
        "polymarket_evidence",
        "divergence",
        "crypto_evidence",
        "comparison",
        "news_evidence",
        "candidate",
    ):
        payload[component]["theme_id"] = "theme_ctx_xrp_bearish"

    payload["comparison"]["polymarket_summary"]["direction"] = "bearish"
    payload["comparison"]["crypto_summary"]["direction"] = "bearish"
    payload["comparison"]["explanation"] = "XRP bearish aligned comparison packet."
    payload["candidate"]["title"] = "XRP Bearish Bridge Signal"
    payload["candidate"]["explanation"] = "XRP bearish candidate signal packet."
    payload["theme_link"]["explanation"] = "Deterministic XRP bearish bridge fixture."

    context_source = tmp_path / "xrp_bearish_context_bundle.json"
    context_source.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return context_source


def _raw_context_case(case_name: str) -> dict[str, Any]:
    payload = json.loads(_CONTEXT_FIXTURE_PATH.read_text(encoding="utf-8"))
    for entry in payload:
        if entry["case"] == case_name:
            return json.loads(json.dumps(entry))
    raise AssertionError(f"missing fixture case: {case_name}")


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
