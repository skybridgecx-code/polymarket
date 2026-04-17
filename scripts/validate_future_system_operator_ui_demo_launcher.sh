#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "error: $*" >&2
  exit 1
}

if [[ ! -f "pyproject.toml" ]]; then
  fail "run this script from repo root (missing pyproject.toml)."
fi

if [[ ! -f "scripts/launch_future_system_operator_ui_demo.sh" ]]; then
  fail "missing launcher script at scripts/launch_future_system_operator_ui_demo.sh."
fi

if [[ ! -d "evidence/local-operator-ui" ]]; then
  fail "missing evidence/local-operator-ui directory."
fi

evidence_before="$(find evidence/local-operator-ui -maxdepth 1 -type f | sort)"

echo "[1/6] Syntax check launcher script..."
bash -n scripts/launch_future_system_operator_ui_demo.sh

echo "[2/6] Ensure bounded temp root sentinel exists..."
mkdir -p .tmp
tmp_sentinel=".tmp/.demo_launcher_validate_keep"
: > "${tmp_sentinel}"

echo "[3/6] Clean demo artifacts and run prepare-only launcher flow..."
make future-system-operator-ui-demo-clean
make future-system-operator-ui-demo-prepare

echo "[4/6] Verify expected deterministic demo artifacts..."
[[ -f ".tmp/future-system-operator-ui-demo/context_bundle.json" ]] || fail "missing context_bundle.json"
[[ -f ".tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.json" ]] || fail "missing review export json"
[[ -f ".tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.md" ]] || fail "missing review export markdown"
[[ -f ".tmp/future-system-operator-ui-demo/operator_runs/theme_ctx_strong.analysis_success_export.operator_review.json" ]] || fail "missing operator review metadata json"

echo "[5/6] Verify cleanup only removes demo temp directory..."
make future-system-operator-ui-demo-clean
[[ ! -e ".tmp/future-system-operator-ui-demo" ]] || fail "demo temp directory still exists after cleanup"
[[ -e "${tmp_sentinel}" ]] || fail "cleanup removed more than demo temp directory under .tmp"

echo "[6/6] Verify evidence directory was not modified..."
evidence_after="$(find evidence/local-operator-ui -maxdepth 1 -type f | sort)"
if [[ "${evidence_before}" != "${evidence_after}" ]]; then
  fail "evidence/local-operator-ui file listing changed during validation"
fi

rm -f "${tmp_sentinel}"

echo "future_system operator UI demo launcher smoke validation passed."
