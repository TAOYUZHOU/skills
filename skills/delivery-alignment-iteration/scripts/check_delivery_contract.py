#!/usr/bin/env python3
"""Validate that an iteration contract contains the minimum alignment fields."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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
    "handoff",
]

V2_REQUIRED_KEYS = ["sandbox", "adversarial_gate"]
ADVERSARIAL_REQUIRED_KEYS = ["risk", "decision", "reason"]
ADVERSARIAL_HIGH_RISK_KEYS = ["base", "candidate", "attack_scope", "evidence_dir"]
HANDOFF_METADATA = ["status", "updated_at_utc", "iteration", "contract"]
HANDOFF_HEADINGS = [
    "intent",
    "non_goals",
    "current_truth",
    "current_phase",
    "completed_changes",
    "verification_evidence",
    "open_blockers_and_risks",
    "exact_next_action",
    "final_claims_allowed_now",
]
V2_HANDOFF_HEADINGS = ["adversarial_gate_evidence"]
HIGH_RISK_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".py",
    ".rs",
    ".sh",
    ".sql",
    ".ts",
    ".tsx",
}
HIGH_RISK_PARTS = {
    ".github",
    "app",
    "bin",
    "harp",
    "lib",
    "runtime",
    "scripts",
    "src",
    "tests",
}


def _read_contract(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _has_key(text: str, key: str) -> bool:
    heading_key_pattern = re.escape(key).replace("_", r"[_\s-]*")
    patterns = [
        rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:",
        rf"(?im)^#+\s*{heading_key_pattern}\s*$",
        rf"(?im)^[ \t]*[-*][ \t]*{re.escape(key)}[ \t]*:",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _has_top_level_key(text: str, key: str) -> bool:
    heading_key_pattern = re.escape(key).replace("_", r"[_\s-]*")
    return bool(
        re.search(rf"(?m)^{re.escape(key)}\s*:", text)
        or re.search(rf"(?im)^#+\s*{heading_key_pattern}\s*$", text)
    )


def _schema_version(text: str) -> tuple[int, str]:
    match = re.search(r"(?m)^schema_version\s*:\s*([^\n#]*)", text)
    if not match:
        return 1, ""
    raw = match.group(1).strip()
    if not re.fullmatch(r"\d+", raw):
        return 0, f"invalid schema_version: {raw or '(empty)'}"
    version = int(raw)
    if version not in {1, 2}:
        return version, f"unsupported schema_version: {version}"
    return version, ""


def _top_level_block(text: str, key: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(key)}[ \t]*:[ \t]*(.*?)(?=^[A-Za-z_][A-Za-z0-9_]*[ \t]*:|\Z)",
        text,
    )
    return match.group(1) if match else ""


def _scalar_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:[ \t]*([^\n#]+)", text)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


def _top_level_field_nonempty(text: str, key: str) -> bool:
    yaml_match = re.search(rf"(?m)^{re.escape(key)}\s*:\s*([^\n#]*)", text)
    if yaml_match:
        if yaml_match.group(1).strip():
            return True
        tail = text[yaml_match.end() :]
        block = re.split(r"(?m)^(?:[A-Za-z_][A-Za-z0-9_]*\s*:|#+\s+)", tail, maxsplit=1)[0]
        return bool(block.strip())
    heading_key_pattern = re.escape(key).replace("_", r"[_\s-]*")
    heading = re.search(rf"(?im)^#+\s*{heading_key_pattern}\s*$", text)
    if not heading:
        return False
    tail = text[heading.end() :]
    body = re.split(r"(?m)^#+\s+", tail, maxsplit=1)[0]
    return bool(body.strip())


def _nested_field_nonempty(block: str, key: str) -> bool:
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:[ \t]*([^\n#]*)", block)
    if not match:
        return False
    if match.group(1).strip():
        return True
    tail = block[match.end() :]
    nested = re.split(
        r"(?m)^[ \t]*[A-Za-z_][A-Za-z0-9_]*[ \t]*:", tail, maxsplit=1
    )[0]
    return bool(nested.strip())


def _nested_list_values(block: str, key: str) -> list[str]:
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:[ \t]*([^\n#]*)", block)
    if not match:
        return []
    inline = match.group(1).strip()
    if inline.startswith("[") and inline.endswith("]"):
        return [
            part.strip().strip("'\"")
            for part in inline[1:-1].split(",")
            if part.strip().strip("'\"")
        ]
    tail = block[match.end() :]
    nested = re.split(
        r"(?m)^[ \t]*[A-Za-z_][A-Za-z0-9_]*[ \t]*:", tail, maxsplit=1
    )[0]
    return [
        item.strip().strip("'\"")
        for item in re.findall(r"(?m)^[ \t]*-[ \t]+(.+?)[ \t]*$", nested)
        if item.strip().strip("'\"")
    ]


def validate(text: str) -> dict:
    version, version_error = _schema_version(text)
    required = REQUIRED_KEYS + (V2_REQUIRED_KEYS if version >= 2 else [])
    missing = [key for key in required if not _has_top_level_key(text, key)]
    empty_required = [
        key
        for key in required
        if key not in missing and not _top_level_field_nonempty(text, key)
    ]
    adversarial_errors = []
    if version >= 2 and "adversarial_gate" not in missing:
        block = _top_level_block(text, "adversarial_gate")
        for key in ADVERSARIAL_REQUIRED_KEYS:
            if not _has_key(block, key):
                adversarial_errors.append(f"missing adversarial_gate.{key}")
            elif not _nested_field_nonempty(block, key):
                adversarial_errors.append(f"empty adversarial_gate.{key}")
        risk = _scalar_value(block, "risk").lower()
        decision = _scalar_value(block, "decision").lower()
        if risk not in {"high", "low"}:
            adversarial_errors.append("adversarial_gate.risk must be high or low")
        if decision not in {"required", "skipped"}:
            adversarial_errors.append("adversarial_gate.decision must be required or skipped")
        if risk == "high":
            if decision != "required":
                adversarial_errors.append("high-risk diff requires decision: required")
            for key in ADVERSARIAL_HIGH_RISK_KEYS:
                if not _has_key(block, key):
                    adversarial_errors.append(f"missing adversarial_gate.{key}")
                elif not _nested_field_nonempty(block, key):
                    adversarial_errors.append(f"empty adversarial_gate.{key}")
        if risk == "low" and decision != "skipped":
            adversarial_errors.append("low-risk diff must record decision: skipped")
    return {
        "ok": not version_error and not missing and not empty_required and not adversarial_errors,
        "schema_version": version,
        "schema_version_error": version_error,
        "missing_keys": missing,
        "empty_keys": empty_required,
        "adversarial_errors": adversarial_errors,
        "required_keys": required,
    }


def _heading_present(text: str, key: str) -> bool:
    pattern = re.escape(key).replace("_", r"[\s_-]*")
    return bool(re.search(rf"(?im)^#+\s*{pattern}\s*$", text))


def validate_handoff(text: str, *, schema_version: int = 1) -> dict:
    missing_metadata = [key for key in HANDOFF_METADATA if not _has_top_level_key(text, key)]
    required_headings = HANDOFF_HEADINGS + (
        V2_HANDOFF_HEADINGS if schema_version >= 2 else []
    )
    missing_headings = [key for key in required_headings if not _heading_present(text, key)]
    empty_headings = [
        key
        for key in required_headings
        if key not in missing_headings and not _top_level_field_nonempty(text, key)
    ]
    return {
        "ok": not missing_metadata and not missing_headings and not empty_headings,
        "missing_metadata": missing_metadata,
        "missing_headings": missing_headings,
        "empty_headings": empty_headings,
        "required_metadata": HANDOFF_METADATA,
        "required_headings": required_headings,
    }


def validate_current_schema(result: dict) -> dict:
    if int(result.get("schema_version") or 0) == 2:
        return {"ok": True}
    return {
        "ok": False,
        "error": "new/current iterations require schema_version: 2",
    }


def validate_handoff_binding(text: str, root: Path, supplied: Path) -> dict:
    declared = _scalar_value(_top_level_block(text, "handoff"), "path")
    if not declared:
        return {"ok": False, "error": "contract handoff.path is missing"}
    expected = (root.resolve() / declared).resolve()
    actual = supplied.resolve()
    return {
        "ok": expected == actual,
        "declared": str(expected),
        "supplied": str(actual),
    }


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def _path_is_high_risk(path: str) -> bool:
    p = Path(path)
    parts = set(p.parts)
    lowered = p.name.lower()
    if len(p.parts) >= 2 and p.parts[0] == "docs" and p.parts[1] == "evidence":
        return False
    if p.name == "SKILL.md":
        return True
    if parts & HIGH_RISK_PARTS:
        return True
    if p.suffix.lower() in HIGH_RISK_SUFFIXES:
        return True
    return any(token in lowered for token in ("contract", "prompt", "schema", "workflow"))


def validate_diff_binding(text: str, root: Path) -> dict:
    block = _top_level_block(text, "adversarial_gate")
    declared_risk = _scalar_value(block, "risk").lower()
    base = _scalar_value(block, "base")
    candidate = _scalar_value(block, "candidate")
    declared_scope = set(_nested_list_values(block, "attack_scope"))
    result = {
        "ok": False,
        "base": base,
        "candidate": candidate,
        "declared_risk": declared_risk,
        "declared_scope": sorted(declared_scope),
        "changed_paths": [],
        "high_risk_paths": [],
        "missing_from_attack_scope": [],
    }
    if not base or not candidate:
        result["error"] = "base and candidate are required for diff binding"
        return result
    try:
        base_sha = _git(root, "rev-parse", f"{base}^{{commit}}").strip()
        candidate_sha = _git(root, "rev-parse", f"{candidate}^{{commit}}").strip()
        changed = {
            line.strip()
            for line in _git(root, "diff", "--name-only", base_sha, candidate_sha, "--").splitlines()
            if line.strip()
        }
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result
    missing = sorted(changed - declared_scope)
    high_risk_paths = sorted(path for path in changed if _path_is_high_risk(path))
    risk_conflict = declared_risk == "low" and bool(high_risk_paths)
    result.update(
        {
            "ok": not missing and not risk_conflict and bool(changed),
            "base_sha": base_sha,
            "candidate_sha": candidate_sha,
            "changed_paths": sorted(changed),
            "high_risk_paths": high_risk_paths,
            "missing_from_attack_scope": missing,
            "risk_conflict": risk_conflict,
        }
    )
    if not changed:
        result["error"] = "bound diff is empty"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, help="Contract path, or '-' for stdin.")
    parser.add_argument("--handoff", required=True, help="Stable docs handoff SSOT path.")
    parser.add_argument("--root", default=".", help="Repository root for future path checks.")
    parser.add_argument(
        "--require-current-schema",
        action="store_true",
        help="Reject legacy contracts for a new/current iteration.",
    )
    parser.add_argument(
        "--check-diff",
        action="store_true",
        help="Bind high-risk attack_scope to exact base..candidate git paths.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args()

    text = _read_contract(args.contract)
    result = validate(text)
    if args.require_current_schema:
        current_schema = validate_current_schema(result)
        result["current_schema"] = current_schema
        result["ok"] = bool(result["ok"] and current_schema["ok"])
    handoff_path = Path(args.handoff)
    try:
        handoff_text = handoff_path.read_text(encoding="utf-8")
    except OSError as exc:
        handoff_result = {"ok": False, "error": str(exc), "path": str(handoff_path)}
    else:
        handoff_result = validate_handoff(
            handoff_text,
            schema_version=int(result.get("schema_version") or 1),
        )
        handoff_result["path"] = str(handoff_path)
    binding = validate_handoff_binding(text, Path(args.root), handoff_path)
    handoff_result["binding"] = binding
    handoff_result["ok"] = bool(handoff_result.get("ok") and binding["ok"])
    result["handoff"] = handoff_result
    result["ok"] = bool(result["ok"] and handoff_result.get("ok"))
    if args.check_diff:
        diff_result = validate_diff_binding(text, Path(args.root).resolve())
        result["diff_binding"] = diff_result
        result["ok"] = bool(result["ok"] and diff_result.get("ok"))
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
