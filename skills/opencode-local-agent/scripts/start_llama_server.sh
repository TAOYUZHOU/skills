#!/usr/bin/env bash
# Start llama-server with long-context agent profile (single slot, q8 KV, flash-attn).
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK_DIR="${WORK_DIR:-$(pwd)}"

GGUF_PATH="${GGUF_PATH:-}"
LLAMA_SERVER="${LLAMA_SERVER:-}"
LLM_HOST="${LLM_HOST:-0.0.0.0}"
LLM_PORT="${LLM_PORT:-8080}"
PROFILE="${PROFILE:-longctx}"

if [[ -z "$GGUF_PATH" ]]; then
  for candidate in \
    "$WORK_DIR/.cache/local-models/qwythos-9b-q4/Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf" \
    "$WORK_DIR/../qwythos-local/models/Qwythos-9B-Claude-Mythos-5-1M-Q4_K_M.gguf"; do
    if [[ -f "$candidate" ]]; then
      GGUF_PATH="$candidate"
      break
    fi
  done
fi

if [[ -z "$LLAMA_SERVER" ]]; then
  for candidate in \
    "$WORK_DIR/../llama.cpp/build/bin/llama-server" \
    "/root/autodl-tmp/taoyuzhou/llama.cpp/build/bin/llama-server"; do
    if [[ -x "$candidate" ]]; then
      LLAMA_SERVER="$candidate"
      break
    fi
  done
  LLAMA_SERVER="${LLAMA_SERVER:-llama-server}"
fi

if [[ "$PROFILE" == "dev" ]]; then
  CTX="${CTX:-8192}"
  PARALLEL="${PARALLEL:-1}"
  CACHE_TYPE_K="${CACHE_TYPE_K:-f16}"
  CACHE_TYPE_V="${CACHE_TYPE_V:-f16}"
else
  CTX="${CTX:-102400}"
  PARALLEL="${PARALLEL:-1}"
  CACHE_TYPE_K="${CACHE_TYPE_K:-q8_0}"
  CACHE_TYPE_V="${CACHE_TYPE_V:-q8_0}"
fi

NGL="${NGL:-99}"
FLASH_ATTN="${FLASH_ATTN:-on}"
REASONING_PRESERVE="${REASONING_PRESERVE:-on}"

export GGUF_PATH LLAMA_SERVER LLM_HOST LLM_PORT PROFILE CTX PARALLEL CACHE_TYPE_K CACHE_TYPE_V NGL FLASH_ATTN

if [[ ! -f "${GGUF_PATH:-/nonexistent}" ]]; then
  echo "GGUF_PATH not found. Set GGUF_PATH or download via hf-hub skill." >&2
  exit 1
fi

if ! command -v "$LLAMA_SERVER" >/dev/null 2>&1 && [[ ! -x "$LLAMA_SERVER" ]]; then
  echo "LLAMA_SERVER not found: $LLAMA_SERVER" >&2
  exit 1
fi

STATE="$WORK_DIR/.state/opencode_local_agent.json"
mkdir -p "$(dirname "$STATE")"
export STATE CTX PARALLEL CACHE_TYPE_K CACHE_TYPE_V FLASH_ATTN LLM_PORT PROFILE GGUF_PATH
python3 - <<'PY'
import json, os
from pathlib import Path
port = os.environ.get("LLM_PORT", "8080")
Path(os.environ["STATE"]).write_text(
    json.dumps(
        {
            "profile": os.environ.get("PROFILE", "longctx"),
            "gguf_path": os.environ.get("GGUF_PATH", ""),
            "llm_base_url": f"http://127.0.0.1:{port}/v1",
            "n_ctx": int(os.environ.get("CTX", "102400")),
            "parallel": int(os.environ.get("PARALLEL", "1")),
            "cache_type_k": os.environ.get("CACHE_TYPE_K", "q8_0"),
            "cache_type_v": os.environ.get("CACHE_TYPE_V", "q8_0"),
            "flash_attn": os.environ.get("FLASH_ATTN", "on"),
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

echo "Starting llama-server profile=$PROFILE ctx=$CTX parallel=$PARALLEL kv=$CACHE_TYPE_K/$CACHE_TYPE_V"
echo "Template: GGUF embedded (Qwen3.5 v3) reasoning-preserve=$REASONING_PRESERVE"
echo "API: http://127.0.0.1:$LLM_PORT/v1"

exec "$LLAMA_SERVER" \
  -m "$GGUF_PATH" \
  --host "$LLM_HOST" \
  --port "$LLM_PORT" \
  -c "$CTX" \
  -ngl "$NGL" \
  --parallel "$PARALLEL" \
  --flash-attn "$FLASH_ATTN" \
  --cache-type-k "$CACHE_TYPE_K" \
  --cache-type-v "$CACHE_TYPE_V" \
  $([[ "$REASONING_PRESERVE" == "on" ]] && echo --reasoning-preserve)
