#!/usr/bin/env python3
"""Append a compact HARP skill-use audit event."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=["start", "finish", "note"])
    parser.add_argument("--reason", default="")
    parser.add_argument("--artifact", default="")
    parser.add_argument("--skill", default="opencode-local-agent")
    args = parser.parse_args()

    work_dir = Path(os.environ.get("WORK_DIR") or os.getcwd())
    state_dir = work_dir / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "skill": args.skill,
        "event": args.event,
        "reason": args.reason,
        "artifact": args.artifact,
        "cwd": os.getcwd(),
    }
    with (state_dir / "skill_usage_ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
