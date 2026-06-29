#!/usr/bin/env bash
# Write opencode.json from skill template into a project directory.
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-${WORK_DIR:-$(pwd)}}"
TARGET="$(cd "$TARGET" && pwd)"

export LLM_BASE_URL="${LLM_BASE_URL:-http://127.0.0.1:8080/v1}"
export OPENCODE_MODEL_ID="${OPENCODE_MODEL_ID:-qwythos-q4}"
export TEMPLATE="$SKILL_ROOT/templates/opencode.json"
export OUT="$TARGET/opencode.json"
export STATE_DIR="$TARGET/.state"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Missing template: $TEMPLATE" >&2
  exit 1
fi

python3 - <<'PY'
import json
import os
from pathlib import Path

template = json.loads(Path(os.environ["TEMPLATE"]).read_text(encoding="utf-8"))
base_url = os.environ["LLM_BASE_URL"]
model_id = os.environ["OPENCODE_MODEL_ID"]
out = Path(os.environ["OUT"])

template["provider"]["local-llm"]["options"]["baseURL"] = base_url
template["model"] = f"local-llm/{model_id}"
template["small_model"] = f"local-llm/{model_id}"

out.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out}")
print(f"  baseURL={base_url}")
print(f"  model=local-llm/{model_id}")
PY

mkdir -p "$STATE_DIR"
python3 - <<'PY'
import json
import os
from pathlib import Path

state_path = Path(os.environ["STATE_DIR"]) / "opencode_local_agent.json"
payload = {}
if state_path.exists():
    payload = json.loads(state_path.read_text(encoding="utf-8"))
payload.update(
    {
        "opencode_config_path": os.environ["OUT"],
        "llm_base_url": os.environ["LLM_BASE_URL"],
        "opencode_model_id": os.environ["OPENCODE_MODEL_ID"],
    }
)
state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

echo "Next: cd \"$TARGET\" && opencode"
