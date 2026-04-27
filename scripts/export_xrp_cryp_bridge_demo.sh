#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON:-"${repo_root}/.venv/bin/python"}"
output_root="${1:-"${repo_root}/.tmp/cryp-xrp-bridge-demo"}"

context_source="${repo_root}/tests/fixtures/future_system/context_bundle/xrp_bridge_context_bundle.json"
run_id="theme_ctx_xrp_bullish.analysis_success_export"
operator_runs_dir="${output_root}/operator_runs/xrp"
packages_dir="${output_root}/packages"
exports_dir="${output_root}/exports"
output_path="${exports_dir}/xrp_external_confirmation.json"

if [[ "${XRP_BRIDGE_DEMO_PRESERVE_OUTPUT:-0}" != "1" ]]; then
  rm -rf "${operator_runs_dir}" "${packages_dir}/${run_id}.package" "${output_path}"
fi

mkdir -p "${operator_runs_dir}" "${packages_dir}" "${exports_dir}"

"${python_bin}" -m future_system.cli.review_artifacts \
  --context-source "${context_source}" \
  --target-directory "${operator_runs_dir}" \
  --analyst-mode stub \
  --initialize-operator-review

"${python_bin}" - "${operator_runs_dir}" "${run_id}" <<'PY'
from __future__ import annotations

import sys

from future_system.operator_review_models.updates import (
    OperatorReviewDecisionUpdateInput,
    update_existing_operator_review_metadata_companion,
)

target_directory = sys.argv[1]
run_id = sys.argv[2]

update_existing_operator_review_metadata_companion(
    target_directory=target_directory,
    run_id=run_id,
    update_input=OperatorReviewDecisionUpdateInput(
        review_status="decided",
        operator_decision="approve",
        review_notes_summary="Approved deterministic XRP bridge fixture export.",
        reviewer_identity="xrp_bridge_demo",
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

echo "xrp_external_confirmation_path=${output_path}"
