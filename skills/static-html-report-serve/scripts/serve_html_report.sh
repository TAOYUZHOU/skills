#!/usr/bin/env bash
# Serve a static HTML directory on 0.0.0.0 (AutoDL custom service port 6006 by default).
set -euo pipefail

DIR=""
PORT="${REPORT_HTTP_PORT:-6006}"
ENTRY="index.html"
MODE="start"

usage() {
  cat <<'EOF'
Usage: serve_html_report.sh --dir PATH [options]

Options:
  --dir PATH          Document root to serve (required)
  --port PORT         Listen port (default: 6006)
  --entry FILE.html   Primary HTML for public URL hint (default: index.html)
  --stop              Stop server for this directory
  --status            Print pid, log tail, URLs; exit 0 if running
  -h, --help          This help

Env:
  AutoDLService6006URL   Public base URL when port=6006 (set by AutoDL)
  REPORT_HTTP_PORT       Default port override
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="${2:-}"; shift 2 ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --entry) ENTRY="${2:-}"; shift 2 ;;
    --stop) MODE="stop"; shift ;;
    --status) MODE="status"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$DIR" ]]; then
  echo "error: --dir is required" >&2
  usage >&2
  exit 2
fi

DIR="$(cd "$DIR" && pwd)"
PIDFILE="${DIR}/.report_http.pid"
LOG="${DIR}/.report_http.log"

print_urls() {
  local base="${1:-}"
  echo ""
  if [[ -n "$base" && "$PORT" == "6006" ]]; then
    base="${base%/}"
    echo "公网/局域网（AutoDL 自定义服务 6006）："
    echo "  ${base}/${ENTRY}"
    echo "  ${base}/"
  else
    echo "本地: http://127.0.0.1:${PORT}/${ENTRY}"
    echo "请在 AutoDL 控制台将端口 ${PORT} 映射到公网后分享链接。"
  fi
}

if [[ "$MODE" == "stop" ]]; then
  if [[ -f "$PIDFILE" ]]; then
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "Stopped HTTP server for ${DIR}"
  else
    echo "No pidfile: ${PIDFILE}"
  fi
  exit 0
fi

if [[ "$MODE" == "status" ]]; then
  if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "running pid=$(cat "$PIDFILE") dir=${DIR} port=${PORT}"
    print_urls "${AutoDLService6006URL:-}"
    if command -v curl >/dev/null 2>&1; then
      code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${PORT}/${ENTRY}" || echo "000")
      echo "localhost GET /${ENTRY} -> HTTP ${code}"
    fi
    if [[ -f "$LOG" ]]; then
      echo "--- log tail ---"
      tail -n 5 "$LOG" 2>/dev/null || true
    fi
    exit 0
  fi
  echo "not running (dir=${DIR})"
  exit 1
fi

if [[ ! -d "$DIR" ]]; then
  echo "error: directory not found: $DIR" >&2
  exit 1
fi

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Already running (pid $(cat "$PIDFILE")). Log: ${LOG}"
else
  nohup python3 -m http.server "$PORT" --bind 0.0.0.0 --directory "$DIR" \
    >>"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  sleep 0.5
  if ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "error: server failed to start; see ${LOG}" >&2
    exit 1
  fi
  echo "Started HTTP server on 0.0.0.0:${PORT} (pid $(cat "$PIDFILE"))"
  echo "Document root: ${DIR}"
fi

print_urls "${AutoDLService6006URL:-}"
