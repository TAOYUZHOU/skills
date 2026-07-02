#!/usr/bin/env python3
"""Validate that an iteration contract contains the minimum alignment fields."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_KEYS = [
    "intent",
    "non_goals",
    "ssot",
    "deliverables",
    "acceptance_criteria",
    "verification",
    "traceability",
    "risks",
    "final_claims_allowed",
]


def _read_contract(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _has_key(text: str, key: str) -> bool:
    heading_key_pattern = re.escape(key).replace("_", r"[_\s-]*")
    patterns = [
        rf"(?m)^\s*{re.escape(key)}\s*:",
        rf"(?im)^#+\s*{heading_key_pattern}\s*$",
        rf"(?im)^\s*[-*]\s*{re.escape(key)}\s*:",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def validate(text: str) -> dict:
    missing = [key for key in REQUIRED_KEYS if not _has_key(text, key)]
    empty_required = []
    for key in REQUIRED_KEYS:
        match = re.search(rf"(?ms)^\s*{re.escape(key)}\s*:\s*(.*?)(?=^\s*[A-Za-z_][A-Za-z0-9_]*\s*:|\Z)", text)
        if match and not match.group(1).strip():
            empty_required.append(key)
    return {
        "ok": not missing and not empty_required,
        "missing_keys": missing,
        "empty_keys": empty_required,
        "required_keys": REQUIRED_KEYS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, help="Contract path, or '-' for stdin.")
    parser.add_argument("--root", default=".", help="Repository root for future path checks.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args()

    text = _read_contract(args.contract)
    result = validate(text)
    result["contract"] = args.contract
    result["root"] = str(Path(args.root).resolve())

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print("delivery contract OK")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
