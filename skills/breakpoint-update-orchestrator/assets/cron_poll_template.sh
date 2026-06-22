#!/usr/bin/env bash
set -euo pipefail

# Example cron entry:
# */5 * * * * /path/to/cron_poll_template.sh >> /tmp/breakpoint_cron.log 2>&1

SKILL_DIR="/root/autodl-tmp/taoyuzhou/skills/skills/breakpoint-update-orchestrator"
CONFIG="/path/to/breakpoint_config.json"
LOCK_FILE="/tmp/breakpoint_update_guard.lock"

flock -n "$LOCK_FILE" python3 "$SKILL_DIR/scripts/breakpoint_guard.py" --config "$CONFIG"
