#!/usr/bin/env python3
"""Block new launches, wait for active workers to drain, then trigger update commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_jsonl(path: Path | None, payload: dict) -> None:
    row = {"time": utc_now(), **payload}
    line = json.dumps(row, ensure_ascii=False)
    if path is None:
        print(line, flush=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ps_rows() -> list[dict]:
    out = subprocess.check_output(["ps", "-eo", "pid=,ppid=,pgid=,stat=,etime=,cmd="], text=True)
    rows = []
    for line in out.splitlines():
        parts = line.strip().split(None, 5)
        if len(parts) < 6:
            continue
        pid, ppid, pgid, stat, etime, cmd = parts
        rows.append({"pid": int(pid), "ppid": int(ppid), "pgid": int(pgid), "stat": stat, "etime": etime, "cmd": cmd})
    return rows


def match_rows(patterns: list[str], ignore_pids: set[int]) -> list[dict]:
    if not patterns:
        return []
    compiled = [re.compile(p) for p in patterns]
    rows = []
    for row in ps_rows():
        if row["pid"] in ignore_pids:
            continue
        if "breakpoint_guard.py" in row["cmd"]:
            continue
        if any(p.search(row["cmd"]) for p in compiled):
            rows.append(row)
    return rows


def write_block_file(path: Path | None, reason: str, dry_run: bool) -> None:
    if path is None:
        return
    payload = {"created_at": utc_now(), "reason": reason, "pid": os.getpid()}
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def signal_pids(rows: list[dict], sig: signal.Signals, dry_run: bool, status: Path | None, event: str) -> None:
    for row in rows:
        append_jsonl(status, {"event": event, "pid": row["pid"], "signal": sig.name, "cmd": row["cmd"]})
        if not dry_run:
            try:
                os.kill(row["pid"], sig)
            except ProcessLookupError:
                append_jsonl(status, {"event": "signal_missed_process", "pid": row["pid"]})


def run_commands(commands: list[str], dry_run: bool, status: Path | None, event_prefix: str) -> None:
    for cmd in commands:
        append_jsonl(status, {"event": f"{event_prefix}_start", "command": cmd})
        if dry_run:
            continue
        proc = subprocess.run(cmd, shell=True)
        append_jsonl(status, {"event": f"{event_prefix}_finish", "command": cmd, "returncode": proc.returncode})
        if proc.returncode != 0:
            raise SystemExit(f"command failed: {cmd}")


def as_list(cli_values: list[str] | None, config: dict, key: str) -> list[str]:
    if cli_values:
        return cli_values
    value = config.get(key, [])
    if isinstance(value, str):
        return [value]
    return list(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--worker-pattern", action="append")
    parser.add_argument("--launcher-pattern", action="append")
    parser.add_argument("--mode", choices=["cooperative", "freeze-launchers", "terminate-launchers"], default=None)
    parser.add_argument("--block-file", type=Path)
    parser.add_argument("--status-jsonl", type=Path)
    parser.add_argument("--poll-sec", type=float)
    parser.add_argument("--timeout-sec", type=float)
    parser.add_argument("--reason", default="breakpoint update requested")
    parser.add_argument("--on-ready", action="append")
    parser.add_argument("--restart-command", action="append")
    parser.add_argument("--remove-block-on-success", action="store_true")
    parser.add_argument("--terminate-frozen-launchers-on-success", action="store_true")
    parser.add_argument("--resume-launchers-on-timeout", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    worker_patterns = as_list(args.worker_pattern, config, "worker_patterns")
    launcher_patterns = as_list(args.launcher_pattern, config, "launcher_patterns")
    mode = args.mode or config.get("mode", "cooperative")
    block_file = args.block_file or (Path(config["block_file"]) if config.get("block_file") else None)
    status = args.status_jsonl or (Path(config["status_jsonl"]) if config.get("status_jsonl") else None)
    poll_sec = float(args.poll_sec if args.poll_sec is not None else config.get("poll_sec", 30))
    timeout_sec = float(args.timeout_sec if args.timeout_sec is not None else config.get("timeout_sec", 0))
    reason = str(config.get("reason", args.reason))
    if args.reason != parser.get_default("reason"):
        reason = args.reason
    on_ready = as_list(args.on_ready, config, "on_ready_commands")
    restart_commands = as_list(args.restart_command, config, "restart_commands")
    remove_block = bool(args.remove_block_on_success or config.get("remove_block_on_success", False))
    terminate_frozen = bool(args.terminate_frozen_launchers_on_success or config.get("terminate_frozen_launchers_on_success", False))
    resume_on_timeout = bool(args.resume_launchers_on_timeout or config.get("resume_launchers_on_timeout", False))

    ignore_pids = {os.getpid()}
    write_block_file(block_file, reason, args.dry_run)
    append_jsonl(
        status,
        {
            "event": "guard_start",
            "mode": mode,
            "worker_patterns": worker_patterns,
            "launcher_patterns": launcher_patterns,
            "block_file": str(block_file) if block_file else None,
            "dry_run": args.dry_run,
            "reason": reason,
        },
    )

    launchers = match_rows(launcher_patterns, ignore_pids)
    frozen_pids = [row["pid"] for row in launchers]
    if mode == "freeze-launchers":
        signal_pids(launchers, signal.SIGSTOP, args.dry_run, status, "freeze_launcher")
    elif mode == "terminate-launchers":
        signal_pids(launchers, signal.SIGTERM, args.dry_run, status, "terminate_launcher")
    elif mode == "cooperative":
        append_jsonl(status, {"event": "cooperative_block_only", "launcher_matches": launchers})

    if args.dry_run:
        workers = match_rows(worker_patterns, ignore_pids)
        append_jsonl(status, {"event": "dry_run_matches", "launchers": launchers, "workers": workers})
        return

    start = time.time()
    try:
        while True:
            workers = match_rows(worker_patterns, ignore_pids)
            append_jsonl(
                status,
                {
                    "event": "poll",
                    "active_workers": len(workers),
                    "workers": [{"pid": w["pid"], "stat": w["stat"], "etime": w["etime"], "cmd": w["cmd"][:240]} for w in workers],
                },
            )
            if not workers:
                break
            if timeout_sec > 0 and time.time() - start > timeout_sec:
                append_jsonl(status, {"event": "timeout", "elapsed_sec": round(time.time() - start, 3)})
                if mode == "freeze-launchers" and resume_on_timeout:
                    signal_pids([{"pid": pid, "cmd": "frozen launcher"} for pid in frozen_pids], signal.SIGCONT, False, status, "resume_launcher_timeout")
                raise SystemExit(2)
            time.sleep(poll_sec)

        append_jsonl(status, {"event": "drain_complete"})
        if mode == "freeze-launchers" and terminate_frozen:
            signal_pids([{"pid": pid, "cmd": "frozen launcher"} for pid in frozen_pids], signal.SIGTERM, False, status, "terminate_frozen_launcher")
        run_commands(on_ready, False, status, "on_ready")
        run_commands(restart_commands, False, status, "restart")
        if remove_block and block_file and block_file.exists():
            block_file.unlink()
            append_jsonl(status, {"event": "block_file_removed", "block_file": str(block_file)})
        append_jsonl(status, {"event": "guard_complete"})
    except KeyboardInterrupt:
        append_jsonl(status, {"event": "interrupted"})
        raise


if __name__ == "__main__":
    main()
