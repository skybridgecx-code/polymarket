from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "export_multi_asset_cryp_bridge_demo.sh"
_XRP_SCRIPT_PATH = _REPO_ROOT / "scripts" / "export_xrp_cryp_bridge_demo.sh"


def _script_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHON"] = sys.executable
    return env


def test_multi_asset_cryp_bridge_demo_exports_manifest_and_all_assets(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "multi_asset_demo"

    result = subprocess.run(
        [str(_SCRIPT_PATH), str(output_root)],
        cwd=_REPO_ROOT,
        env=_script_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest_path = output_root / "exports" / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_kind"] == "cryp_multi_asset_bridge_demo_manifest_v1"
    assert manifest["asset_count"] == 4

    expected_mapping = {
        "BTC": "BTCUSD",
        "ETH": "ETHUSD",
        "SOL": "SOLUSD",
        "XRP": "XRPUSD",
    }
    assets = {entry["source_symbol"]: entry for entry in manifest["assets"]}
    assert set(assets) == set(expected_mapping)

    for source_symbol, expected_cryp_asset in expected_mapping.items():
        asset_lower = source_symbol.lower()
        output_path = output_root / "exports" / f"{asset_lower}_external_confirmation.json"
        assert output_path.exists()

        exported_payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert exported_payload["artifact_kind"] == "external_confirmation_advisory_v1"
        assert exported_payload["asset"] == expected_cryp_asset
        assert exported_payload["directional_bias"] == "buy"
        assert exported_payload["source_system"] == "polymarket-arb"
        assert exported_payload["veto_trade"] is False

        manifest_entry = assets[source_symbol]
        assert manifest_entry["cryp_asset"] == expected_cryp_asset
        assert manifest_entry["directional_bias"] == "buy"
        assert manifest_entry["status"] == "exported"
        assert Path(str(manifest_entry["output_path"])).exists()
        assert Path(str(manifest_entry["source_package_dir"])).exists()
        assert Path(str(manifest_entry["source_json_artifact_path"])).exists()


def test_multi_asset_cryp_bridge_demo_rejects_unsupported_assets(
    tmp_path: Path,
) -> None:
    env = _script_env()
    env["CRYP_BRIDGE_DEMO_ASSETS"] = "DOGE"

    result = subprocess.run(
        [str(_SCRIPT_PATH), str(tmp_path / "bad_asset_demo")],
        cwd=_REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unsupported_cryp_bridge_demo_asset: DOGE" in result.stderr


def test_existing_xrp_cryp_bridge_demo_script_still_exports(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "xrp_demo"

    result = subprocess.run(
        [str(_XRP_SCRIPT_PATH), str(output_root)],
        cwd=_REPO_ROOT,
        env=_script_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output_path = output_root / "exports" / "xrp_external_confirmation.json"
    assert output_path.exists()

    exported_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exported_payload["artifact_kind"] == "external_confirmation_advisory_v1"
    assert exported_payload["asset"] == "XRPUSD"
    assert exported_payload["directional_bias"] == "buy"
    assert exported_payload["source_system"] == "polymarket-arb"
    assert exported_payload["veto_trade"] is False
