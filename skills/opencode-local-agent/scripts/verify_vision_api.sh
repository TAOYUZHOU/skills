#!/usr/bin/env bash
# Verify llama-server vision (mmproj) is loaded.
set -euo pipefail

LLM_PORT="${LLM_PORT:-8080}"
BASE="http://127.0.0.1:${LLM_PORT}"

curl -sf "${BASE}/health" >/dev/null || {
  echo "llama-server not healthy at ${BASE}/health" >&2
  exit 1
}

MOD="$(curl -sf "${BASE}/props" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("modalities",{}).get("vision"))')"
if [[ "$MOD" != "True" && "$MOD" != "true" ]]; then
  echo "vision=false — download mmproj and restart:" >&2
  echo "  bash scripts/download_mmproj.sh" >&2
  echo "  bash scripts/start_llama_server.sh" >&2
  exit 1
fi

echo "modalities.vision=true"
echo "verify_vision_api: OK"
