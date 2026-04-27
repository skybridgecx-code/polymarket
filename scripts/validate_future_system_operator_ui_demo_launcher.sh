#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "error: $*" >&2
  exit 1
}

step() {
  local label="$1"
  shift
  echo ""
  echo "[${label}] $*"
}

assert_non_empty_file() {
  local path="$1"
  [[ -s "${path}" ]] || fail "expected non-empty file: ${path}"
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

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  fail "could not find Python interpreter (.venv/bin/python or python3)."
fi

DEMO_ROOT=".tmp/future-system-operator-ui-demo"
RUN_ID="theme_ctx_strong.analysis_success_export"
CONTEXT_BUNDLE_PATH="${DEMO_ROOT}/context_bundle.json"
RUNS_ROOT_PATH="${DEMO_ROOT}/operator_runs"
REVIEW_JSON_PATH="${RUNS_ROOT_PATH}/${RUN_ID}.json"
REVIEW_MD_PATH="${RUNS_ROOT_PATH}/${RUN_ID}.md"
REVIEW_METADATA_PATH="${RUNS_ROOT_PATH}/${RUN_ID}.operator_review.json"
TMP_SENTINEL_PATH=".tmp/demo-validation-sentinel"

cleanup_tmp_state() {
  rm -f "${TMP_SENTINEL_PATH}"
  make future-system-operator-ui-demo-clean >/dev/null 2>&1 || true
}

trap cleanup_tmp_state EXIT

evidence_before="$(find evidence/local-operator-ui -maxdepth 1 -type f | sort)"

step "1/10" "Syntax check launcher script"
bash -n scripts/launch_future_system_operator_ui_demo.sh

step "2/10" "Create .tmp sentinel used to verify bounded cleanup"
mkdir -p .tmp
: > "${TMP_SENTINEL_PATH}"
[[ -f "${TMP_SENTINEL_PATH}" ]] || fail "failed to create sentinel file ${TMP_SENTINEL_PATH}"

step "3/10" "Run cleanup preflight and confirm .tmp sentinel is preserved"
make future-system-operator-ui-demo-clean
[[ -e "${TMP_SENTINEL_PATH}" ]] || fail "cleanup removed .tmp sentinel (${TMP_SENTINEL_PATH})"
[[ ! -e "${DEMO_ROOT}" ]] || fail "cleanup did not remove ${DEMO_ROOT}"

step "4/10" "Run prepare-only launcher flow"
make future-system-operator-ui-demo-prepare

step "5/10" "Verify generated files exist and are non-empty"
assert_non_empty_file "${CONTEXT_BUNDLE_PATH}"
assert_non_empty_file "${REVIEW_JSON_PATH}"
assert_non_empty_file "${REVIEW_MD_PATH}"
assert_non_empty_file "${REVIEW_METADATA_PATH}"

step "6/10" "Verify companion operator review metadata contract"
if ! "${PYTHON_BIN}" - "${REVIEW_METADATA_PATH}" "${RUN_ID}" <<'PY'
import json
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
expected_run_id = sys.argv[2]

payload = json.loads(metadata_path.read_text(encoding="utf-8"))
errors = []

if payload.get("review_status") != "pending":
    errors.append("review_status must be 'pending'.")
if payload.get("operator_decision", "__missing__") is not None:
    errors.append("operator_decision must be null.")

run_id = payload.get("run_id")
if run_id is None:
    artifact = payload.get("artifact")
    if isinstance(artifact, dict):
        run_id = artifact.get("run_id")
if run_id != expected_run_id:
    errors.append(f"run_id must be '{expected_run_id}', found {run_id!r}.")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)
PY
then
  fail "operator review metadata content validation failed for ${REVIEW_METADATA_PATH}"
fi

step "7/10" "Verify generated review JSON status/run context"
if ! "${PYTHON_BIN}" - "${REVIEW_JSON_PATH}" <<'PY'
import json
import sys
from pathlib import Path

review_path = Path(sys.argv[1])
payload = json.loads(review_path.read_text(encoding="utf-8"))
errors = []

if payload.get("status") != "success":
    errors.append("status must be 'success'.")
if payload.get("theme_id") != "theme_ctx_strong":
    errors.append("theme_id must be 'theme_ctx_strong'.")
if payload.get("export_kind") != "analysis_success_export":
    errors.append("export_kind must be 'analysis_success_export'.")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)
PY
then
  fail "review export json content validation failed for ${REVIEW_JSON_PATH}"
fi

step "8/10" "Run cleanup and verify only demo directory is removed"
make future-system-operator-ui-demo-clean
[[ ! -e "${DEMO_ROOT}" ]] || fail "demo temp directory still exists after cleanup"
[[ -e "${TMP_SENTINEL_PATH}" ]] || fail "cleanup removed more than demo temp directory under .tmp"

step "9/10" "Verify evidence directory remains present and unchanged"
[[ -d "evidence/local-operator-ui" ]] || fail "missing evidence/local-operator-ui after validation"
evidence_after="$(find evidence/local-operator-ui -maxdepth 1 -type f | sort)"
if [[ "${evidence_before}" != "${evidence_after}" ]]; then
  fail "evidence/local-operator-ui file listing changed during validation"
fi

step "10/10" "Remove validation sentinel"
rm -f "${TMP_SENTINEL_PATH}"

echo ""
echo "future_system operator UI demo launcher smoke validation passed (hardened checks)."
