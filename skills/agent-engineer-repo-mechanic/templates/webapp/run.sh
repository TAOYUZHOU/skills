#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
echo "open http://127.0.0.1:8000"
exec uvicorn app:app --host 127.0.0.1 --port 8000
