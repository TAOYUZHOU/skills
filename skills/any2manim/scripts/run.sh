#!/usr/bin/env bash
# Start the Any2Manim server.
#   A2M_HOST (default 127.0.0.1)  A2M_PORT (default 8848)
# Pass extra uvicorn args through, e.g. scripts/run.sh --reload
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # skills/any2manim
APP="$HERE/app"
HOST="${A2M_HOST:-127.0.0.1}"
PORT="${A2M_PORT:-8848}"

cd "$APP"

if [ ! -x .venv/bin/python ]; then
  echo "[any2manim] venv missing — run scripts/setup.sh first" >&2
  exit 1
fi

echo "[any2manim] http://${HOST}:${PORT}"
exec ./.venv/bin/python -m uvicorn backend.main:app --host "$HOST" --port "$PORT" "$@"
