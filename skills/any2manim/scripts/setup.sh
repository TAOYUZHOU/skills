#!/usr/bin/env bash
# Build the Any2Manim virtualenv and install dependencies.
# Idempotent: re-run after pulling new upstream code to refresh deps.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # skills/any2manim
APP="$HERE/app"
PY="${PYTHON:-python3}"

cd "$APP"

if [ ! -d .venv ]; then
  echo "[any2manim] creating venv in $APP/.venv"
  "$PY" -m venv .venv
fi

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# Pre-fetch static-ffmpeg (with libass, for subtitle burn-in) once.
./.venv/bin/python -c "from backend import config; config.ffmpeg_bins()" >/dev/null 2>&1 || true

echo "[any2manim] ready. Start with: $HERE/scripts/run.sh"
