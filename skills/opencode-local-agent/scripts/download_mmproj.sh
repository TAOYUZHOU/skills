#!/usr/bin/env bash
# Download Qwythos vision projector (mmproj) for image input (~0.9 GiB).
set -euo pipefail

WORK_DIR="${WORK_DIR:-$(pwd)}"
MODELS_DIR="${MODELS_DIR:-$WORK_DIR/.cache/local-models/qwythos-9b-q4}"

# Fallback: sibling qwythos-local deployment
if [[ ! -d "$MODELS_DIR" && -d "$WORK_DIR/../qwythos-local/models" ]]; then
  MODELS_DIR="$WORK_DIR/../qwythos-local/models"
fi

MMPROJ_NAME="mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf"
MMPROJ_PATH="$MODELS_DIR/$MMPROJ_NAME"

mkdir -p "$MODELS_DIR"

if [[ -f "$MMPROJ_PATH" ]]; then
  echo "Already present: $MMPROJ_PATH"
  exit 0
fi

echo "Downloading $MMPROJ_NAME → $MODELS_DIR"
hf download empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF \
  --include "$MMPROJ_NAME" \
  --local-dir "$MODELS_DIR"

echo "Done: $MMPROJ_PATH"
echo "Restart llama-server with MMPROJ=$MMPROJ_PATH bash scripts/start_llama_server.sh"
