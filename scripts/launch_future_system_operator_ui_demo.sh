#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f "pyproject.toml" ]]; then
  echo "error: run this script from the repo root (missing pyproject.toml)." >&2
  exit 1
fi

if [[ ! -f "tests/fixtures/future_system/context_bundle/context_bundle_inputs.json" ]]; then
  echo "error: missing fixture input file tests/fixtures/future_system/context_bundle/context_bundle_inputs.json." >&2
  exit 1
fi

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "error: could not find Python interpreter (.venv/bin/python or python3)." >&2
  exit 1
fi

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="src:${PYTHONPATH}"
else
  export PYTHONPATH="src"
fi

PORT="${PORT:-8000}"
PREPARE_ONLY="${PREPARE_ONLY:-0}"

if ! "$PYTHON_BIN" - "$PORT" <<'PY'
import sys

try:
    port = int(sys.argv[1])
except Exception:
    raise SystemExit(1)

if port < 1 or port > 65535:
    raise SystemExit(1)
PY
then
  echo "error: PORT must be an integer between 1 and 65535." >&2
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY'
try:
    import python_multipart  # type: ignore[import-not-found]
except Exception:
    try:
        import multipart  # type: ignore[import-not-found]
    except Exception:
        raise SystemExit(1)
PY
then
  echo "error: missing required package python-multipart for local Uvicorn form handling." >&2
  echo "install command:" >&2
  echo ".venv/bin/python -m pip install python-multipart" >&2
  exit 1
fi

DEMO_ROOT=".tmp/future-system-operator-ui-demo"
ARTIFACTS_ROOT="${DEMO_ROOT}/operator_runs"
CONTEXT_SOURCE="${DEMO_ROOT}/context_bundle.json"

rm -rf "${DEMO_ROOT}"
mkdir -p "${ARTIFACTS_ROOT}"

"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

from future_system.candidates.models import CandidateSignalPacket
from future_system.comparison.models import ThemeComparisonPacket
from future_system.context_bundle.builder import build_opportunity_context_bundle
from future_system.crypto_evidence.models import ThemeCryptoEvidencePacket
from future_system.divergence.models import ThemeDivergencePacket
from future_system.evidence.models import ThemeEvidencePacket
from future_system.news_evidence.models import ThemeNewsEvidencePacket
from future_system.theme_graph.models import ThemeLinkPacket

fixture_path = Path("tests/fixtures/future_system/context_bundle/context_bundle_inputs.json")
fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))

cases = {
    entry["case"]: {
        "theme_link": ThemeLinkPacket.model_validate(entry["theme_link"]),
        "polymarket_evidence": ThemeEvidencePacket.model_validate(entry["polymarket_evidence"]),
        "divergence": ThemeDivergencePacket.model_validate(entry["divergence"]),
        "crypto_evidence": ThemeCryptoEvidencePacket.model_validate(entry["crypto_evidence"]),
        "comparison": ThemeComparisonPacket.model_validate(entry["comparison"]),
        "news_evidence": ThemeNewsEvidencePacket.model_validate(entry["news_evidence"]),
        "candidate": CandidateSignalPacket.model_validate(entry["candidate"]),
    }
    for entry in fixture_payload
}

if "strong_complete" not in cases:
    raise SystemExit("error: missing required fixture case 'strong_complete'.")

strong_case = cases["strong_complete"]
bundle = build_opportunity_context_bundle(
    theme_link_packet=strong_case["theme_link"],
    polymarket_evidence_packet=strong_case["polymarket_evidence"],
    divergence_packet=strong_case["divergence"],
    crypto_evidence_packet=strong_case["crypto_evidence"],
    comparison_packet=strong_case["comparison"],
    news_evidence_packet=strong_case["news_evidence"],
    candidate_packet=strong_case["candidate"],
)

context_source_path = Path(".tmp/future-system-operator-ui-demo/context_bundle.json")
context_source_path.write_text(
    json.dumps(bundle.model_dump(mode="json"), sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
PY

echo "demo context bundle written to: ${CONTEXT_SOURCE}"
echo "demo artifacts directory: ${ARTIFACTS_ROOT}"

CLI_SUMMARY="$("${PYTHON_BIN}" -m future_system.cli.review_artifacts \
  --context-source "${CONTEXT_SOURCE}" \
  --target-directory "${ARTIFACTS_ROOT}" \
  --analyst-mode stub \
  --initialize-operator-review)"
echo "${CLI_SUMMARY}"

RUN_ID="$("$PYTHON_BIN" - "${CLI_SUMMARY}" <<'PY'
import json
import sys
from pathlib import Path

summary = json.loads(sys.argv[1])
json_file_path = summary.get("json_file_path")
if not isinstance(json_file_path, str) or not json_file_path:
    raise SystemExit("error: cli summary missing json_file_path.")
print(Path(json_file_path).stem)
PY
)"

ARTIFACTS_ROOT_ABS="$(cd "${ARTIFACTS_ROOT}" && pwd)"
export FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT="${ARTIFACTS_ROOT_ABS}"
LIST_URL="http://127.0.0.1:${PORT}"
DETAIL_URL="${LIST_URL}/runs/${RUN_ID}"

echo ""
echo "artifact root: ${FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT}"
echo "run id: ${RUN_ID}"
echo "selected port: ${PORT}"
echo "list URL: ${LIST_URL}"
echo "detail URL: ${DETAIL_URL}"

if [[ "${PREPARE_ONLY}" == "1" ]]; then
  echo "PREPARE_ONLY=1 set; Uvicorn was not started."
  exit 0
fi

if ! "$PYTHON_BIN" - "$PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(1)
PY
then
  echo "Port ${PORT} is already in use." >&2
  echo "Try: PORT=8001 make future-system-operator-ui-demo" >&2
  exit 1
fi

echo ""
echo "starting uvicorn (ctrl+c to stop)..."

exec "${PYTHON_BIN}" -m uvicorn future_system.operator_ui.app_entry:create_operator_ui_app --factory --reload --port "${PORT}"
