#!/usr/bin/env bash
# Smoke-test OpenCode agent against local llama-server (headless-safe via pseudo-TTY).
set -euo pipefail

WORK_DIR="${1:-${WORK_DIR:-$(pwd)}}"
WORK_DIR="$(cd "$WORK_DIR" && pwd)"

LLM_PORT="${LLM_PORT:-8080}"
MODEL="${OPENCODE_MODEL:-local-llm/qwythos-q4}"
PROMPT="${OPENCODE_SMOKE_PROMPT:-Reply with exactly: ok}"
TIMEOUT_SEC="${OPENCODE_SMOKE_TIMEOUT:-120}"

if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode CLI not found. Install: npm i -g opencode-ai" >&2
  exit 1
fi

if ! curl -sf "http://127.0.0.1:${LLM_PORT}/health" >/dev/null; then
  echo "llama-server not healthy on port ${LLM_PORT}" >&2
  exit 1
fi

if [[ ! -f "$WORK_DIR/opencode.json" ]]; then
  echo "Missing $WORK_DIR/opencode.json — run setup_opencode_config.sh first" >&2
  exit 1
fi

AUTH="$HOME/.local/share/opencode/auth.json"
mkdir -p "$(dirname "$AUTH")"
export AUTH
python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["AUTH"])
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault("local-llm", {"type": "api", "key": "sk-local"})
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT

export WORK_DIR MODEL PROMPT
# OpenCode init blocks without a TTY in headless shells; `script` provides a pseudo-TTY.
timeout "$TIMEOUT_SEC" script -q -c '
  cd "$WORK_DIR" && opencode run \
    --pure \
    --dangerously-skip-permissions \
    --format json \
    -m "$MODEL" \
    "$PROMPT"
' /dev/null >"$OUT" 2>&1 || {
  echo "verify_opencode_agent: timeout or error after ${TIMEOUT_SEC}s" >&2
  tail -20 "$OUT" >&2 || true
  exit 1
}

export OUT
python3 - <<'PY'
import json, re, os, sys
from pathlib import Path

raw = Path(os.environ["OUT"]).read_text(encoding="utf-8", errors="replace")
text_parts = []
for line in raw.splitlines():
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        evt = json.loads(line)
    except json.JSONDecodeError:
        continue
    part = evt.get("part") or {}
    if part.get("type") == "text":
        text_parts.append(part.get("text") or "")

combined = "\n".join(text_parts)
visible = re.sub(r"<think>.*?</think>", "", combined, flags=re.S).strip()
print("assistant:", visible[:300].replace("\n", " "))
if not visible:
    sys.exit("no assistant text in opencode json stream")
if "ok" not in visible.lower():
    sys.exit(f"expected 'ok' in response, got: {visible[:200]!r}")
PY

echo "verify_opencode_agent: OK"
