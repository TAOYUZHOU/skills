#!/usr/bin/env bash
set -euo pipefail

LLM_PORT="${LLM_PORT:-8080}"
BASE="http://127.0.0.1:${LLM_PORT}"

curl -sf "${BASE}/health" >/dev/null || {
  echo "llama-server not healthy at ${BASE}/health" >&2
  exit 1
}
echo "health OK"

curl -sf "${BASE}/props" | python3 -c '
import json, sys
props = json.load(sys.stdin)
gs = props.get("default_generation_settings", {})
print("n_ctx:", gs.get("n_ctx"))
print("total_slots:", props.get("total_slots"))
'

curl -sf "${BASE}/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer no-key' \
  -d '{"model":"qwythos-q4","messages":[{"role":"user","content":"Reply with exactly: pong"}],"max_tokens":64,"temperature":0.6,"top_p":0.95,"top_k":20}' \
  | python3 -c '
import json, sys
data = json.load(sys.stdin)
text = data["choices"][0]["message"]["content"]
print("assistant:", text[:200].replace("\n", " "))
'

echo "verify_llm_api: OK"
