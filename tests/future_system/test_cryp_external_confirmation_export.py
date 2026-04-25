from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Literal

from future_system.cli.cryp_external_confirmation_export import main as export_cli_main
from future_system.execution_boundary_contract.cryp_confirmation_export import (
    build_cryp_external_confirmation_artifact_from_package,
)
from future_system.review_outcome_packaging import write_review_outcome_package

_CRYP_SRC = Path("/Users/muhammadaatif/cryp/src")


def test_reviewed_polymarket_signal_maps_to_expected_cryp_asset(tmp_path: Path) -> None:
    package_dir = _write_reviewed_signal_package(
        tmp_path,
        asset="BTC",
        signal="buy",
    )

    artifact = build_cryp_external_confirmation_artifact_from_package(
        package_dir=package_dir
    )

    assert artifact.asset == "BTCUSD"
    assert artifact.directional_bias == "buy"
    assert artifact.veto_trade is False
    assert artifact.source_system == "polymarket-arb"
    assert artifact.correlation_id == "theme_btc_regulation.analysis_success_export"


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

        artifact = build_cryp_external_confirmation_artifact_from_package(
            package_dir=package_dir
        )

        assert artifact.asset == "ETHUSD"
        assert artifact.directional_bias == expected_bias
        assert artifact.veto_trade is expected_veto


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
                    "rationale": (
                        "Reviewed Polymarket outcome supports the crypto advisory."
                    ),
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
