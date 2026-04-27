#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON:-"${repo_root}/.venv/bin/python"}"
output_root="${1:-"${repo_root}/.tmp/cryp-multi-asset-bridge-demo"}"

template_context_source="${repo_root}/tests/fixtures/future_system/context_bundle/xrp_bridge_context_bundle.json"
operator_runs_root="${output_root}/operator_runs"
packages_dir="${output_root}/packages"
exports_dir="${output_root}/exports"

asset_list="${CRYP_BRIDGE_DEMO_ASSETS:-BTC ETH SOL XRP}"

if [[ "${MULTI_ASSET_BRIDGE_DEMO_PRESERVE_OUTPUT:-0}" != "1" ]]; then
  rm -rf "${output_root}"
fi

mkdir -p "${operator_runs_root}" "${packages_dir}" "${exports_dir}" "${output_root}/context_bundles"

for source_symbol in ${asset_list}; do
  case "${source_symbol}" in
    BTC) cryp_asset="BTCUSD" ;;
    ETH) cryp_asset="ETHUSD" ;;
    SOL) cryp_asset="SOLUSD" ;;
    XRP) cryp_asset="XRPUSD" ;;
    *)
      echo "unsupported_cryp_bridge_demo_asset: ${source_symbol}" >&2
      exit 2
      ;;
  esac

  asset_lower="$(printf '%s' "${source_symbol}" | tr '[:upper:]' '[:lower:]')"
  theme_id="theme_ctx_${asset_lower}_bullish"
  run_id="${theme_id}.analysis_success_export"
  context_source="${output_root}/context_bundles/${asset_lower}_bridge_context_bundle.json"
  operator_runs_dir="${operator_runs_root}/${asset_lower}"
  output_path="${exports_dir}/${asset_lower}_external_confirmation.json"

  "${python_bin}" - "${template_context_source}" "${context_source}" "${source_symbol}" "${asset_lower}" "${theme_id}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

template_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
asset = sys.argv[3]
asset_lower = sys.argv[4]
theme_id = sys.argv[5]

payload = json.loads(template_path.read_text(encoding="utf-8"))


def rewrite(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): rewrite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite(v) for v in value]
    if isinstance(value, str):
        return (
            value.replace("theme_ctx_xrp_bullish", theme_id)
            .replace("xrp-bullish-bridge-signal", f"{asset_lower}-bullish-bridge-signal")
            .replace("xrp-bridge-demo", f"{asset_lower}-bridge-demo")
            .replace("0xxrpbullish1", f"0x{asset_lower}bullish1")
            .replace("XRP", asset)
            .replace("xrp", asset_lower)
        )
    return value


payload = rewrite(payload)
payload["theme_id"] = theme_id
payload["title"] = f"{asset} Bullish Bridge Signal"
payload["candidate"]["theme_id"] = theme_id
payload["candidate"]["title"] = f"{asset} Bullish Bridge Signal"
payload["candidate"]["primary_symbol"] = asset
payload["candidate"]["primary_market_slug"] = f"{asset_lower}-bullish-bridge-signal"
payload["candidate"]["explanation"] = f"{asset} bullish candidate signal packet."

payload["comparison"]["theme_id"] = theme_id
payload["comparison"]["crypto_summary"]["direction"] = "bullish"
payload["comparison"]["polymarket_summary"]["direction"] = "bullish"

payload["crypto_evidence"]["theme_id"] = theme_id
payload["crypto_evidence"]["primary_symbol"] = f"{asset}-PERP"
payload["crypto_evidence"]["matched_symbols"] = [f"{asset}-PERP"]
payload["crypto_evidence"]["proxy_evidence"][0]["symbol"] = f"{asset}-PERP"

payload["theme_link"]["theme_id"] = theme_id
payload["theme_link"]["matched_assets"][0]["symbol"] = asset
payload["theme_link"]["matched_polymarket_markets"][0]["event_slug"] = f"{asset_lower}-bridge-demo"
payload["theme_link"]["matched_polymarket_markets"][0]["market_slug"] = (
    f"{asset_lower}-bullish-bridge-signal"
)

payload["polymarket_evidence"]["theme_id"] = theme_id
payload["polymarket_evidence"]["primary_market_slug"] = f"{asset_lower}-bullish-bridge-signal"
payload["polymarket_evidence"]["market_evidence"][0]["market_slug"] = (
    f"{asset_lower}-bullish-bridge-signal"
)

payload["divergence"]["theme_id"] = theme_id
payload["divergence"]["primary_market_slug"] = f"{asset_lower}-bullish-bridge-signal"
payload["divergence"]["market_disagreements"][0]["market_slug"] = (
    f"{asset_lower}-bullish-bridge-signal"
)

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  mkdir -p "${operator_runs_dir}"

  "${python_bin}" -m future_system.cli.review_artifacts \
    --context-source "${context_source}" \
    --target-directory "${operator_runs_dir}" \
    --analyst-mode stub \
    --initialize-operator-review

  "${python_bin}" - "${operator_runs_dir}" "${run_id}" "${source_symbol}" <<'PY'
from __future__ import annotations

import sys

from future_system.operator_review_models.updates import (
    OperatorReviewDecisionUpdateInput,
    update_existing_operator_review_metadata_companion,
)

target_directory = sys.argv[1]
run_id = sys.argv[2]
asset = sys.argv[3]

update_existing_operator_review_metadata_companion(
    target_directory=target_directory,
    run_id=run_id,
    update_input=OperatorReviewDecisionUpdateInput(
        review_status="decided",
        operator_decision="approve",
        review_notes_summary=f"Approved deterministic {asset} multi-asset bridge fixture export.",
        reviewer_identity="multi_asset_cryp_bridge_demo",
        updated_at_epoch_ns=1700000000000000100,
    ),
)
PY

  "${python_bin}" -m future_system.cli.review_outcome_package \
    --run-id "${run_id}" \
    --artifacts-root "${operator_runs_dir}" \
    --target-root "${packages_dir}"

  "${python_bin}" -m future_system.cli.cryp_external_confirmation_export \
    --package-dir "${packages_dir}/${run_id}.package" \
    --output-path "${output_path}"

  echo "${asset_lower}_external_confirmation_path=${output_path}"
done

"${python_bin}" - "${output_root}" ${asset_list} <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

output_root = Path(sys.argv[1])
assets = sys.argv[2:]
mapping = {
    "BTC": "BTCUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
}

exports_dir = output_root / "exports"
packages_dir = output_root / "packages"
operator_runs_root = output_root / "operator_runs"

manifest_assets: list[dict[str, object]] = []
for source_symbol in assets:
    if source_symbol not in mapping:
        raise SystemExit(f"unsupported_cryp_bridge_demo_asset: {source_symbol}")

    asset_lower = source_symbol.lower()
    run_id = f"theme_ctx_{asset_lower}_bullish.analysis_success_export"
    output_path = exports_dir / f"{asset_lower}_external_confirmation.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    manifest_assets.append(
        {
            "source_symbol": source_symbol,
            "cryp_asset": mapping[source_symbol],
            "directional_bias": payload["directional_bias"],
            "output_path": str(output_path.resolve()),
            "source_package_dir": str((packages_dir / f"{run_id}.package").resolve()),
            "source_json_artifact_path": str(
                (operator_runs_root / asset_lower / f"{run_id}.json").resolve()
            ),
            "status": "exported",
        }
    )

manifest = {
    "manifest_kind": "cryp_multi_asset_bridge_demo_manifest_v1",
    "asset_count": len(manifest_assets),
    "assets": manifest_assets,
}

manifest_path = exports_dir / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"manifest_path={manifest_path}")
PY
