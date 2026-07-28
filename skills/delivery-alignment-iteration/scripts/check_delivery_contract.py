#!/usr/bin/env python3
"""Validate that an iteration contract contains the minimum alignment fields."""

from __future__ import annotations

import argparse
import html
import hmac
import json
import os
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
ADVERSARIAL_REQUIRED_KEYS = [
    "risk",
    "decision",
    "reason",
    "base",
    "candidate",
    "attack_scope",
    "evidence_dir",
]
ADVERSARIAL_HIGH_RISK_KEYS: list[str] = []
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
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".cjs",
    ".cts",
    ".mjs",
    ".mts",
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
    "tools",
}
LOW_RISK_SUFFIXES = {
    ".bmp",
    ".csv",
    ".gif",
    ".jpeg",
    ".jpg",
    ".md",
    ".pdf",
    ".png",
    ".svg",
    ".txt",
    ".webp",
}
LOW_RISK_DATA_SUFFIXES = {".json"}
HIGH_RISK_FILENAMES = {
    "cargo.lock",
    "cargo.toml",
    "deno.json",
    "deno.jsonc",
    "environment.yml",
    "package-lock.json",
    "package.json",
    "pipfile",
    "pipfile.lock",
    "poetry.lock",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
}
SANDBOX_REQUIRED_KEYS = ["scope", "fixture", "invoke", "assert", "record"]
GATE_EVIDENCE_FILES = [
    "prompt.md",
    "final_agent_output.json",
    "agent_attack_manifest.json",
    "live_provider_receipt.json",
    "gate_result.json",
]


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
    matches = re.findall(r"(?m)^schema_version[ \t]*:[ \t]*([^\n#]*)", text)
    if not matches:
        return 1, ""
    if len(matches) != 1:
        return 0, "duplicate schema_version declarations"
    raw = matches[0].strip()
    if raw not in {"1", "2"}:
        return 0, f"invalid schema_version: {raw or '(empty)'}"
    version = int(raw)
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


def _semantic_scalar_nonempty(raw: str) -> bool:
    value = _strip_html_comments(re.sub(r"(?m)^[ \t]*#.*$", "", raw)).strip()
    if value in {"", "''", '""', "~", "null", "Null", "NULL"}:
        return False
    if re.fullmatch(r"\[\s*\]|\{\s*\}", value):
        return False
    if re.fullmatch(r"[|>][-+]?[1-9]?", value):
        return False
    return True


def _strip_fenced_blocks(text: str) -> str:
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", text)


def _strip_html_comments(text: str) -> str:
    return re.sub(r"(?s)<!--.*?-->", "", text)


def _strip_html_tags(text: str) -> str:
    return re.sub(r"(?s)<[^>]*>", "", text)


def _top_level_field_nonempty(text: str, key: str) -> bool:
    text = _strip_fenced_blocks(text)
    yaml_match = re.search(
        rf"(?m)^{re.escape(key)}[ \t]*:[ \t]*([^\n#]*)", text
    )
    if yaml_match:
        if _semantic_scalar_nonempty(yaml_match.group(1)):
            return True
        tail = text[yaml_match.end() :]
        block = re.split(
            r"(?m)^(?:[A-Za-z_][A-Za-z0-9_]*[ \t]*:|#+[ \t]+)",
            tail,
            maxsplit=1,
        )[0]
        body = _strip_html_comments(block).strip()
        return _semantic_body_nonempty(body)
    heading_key_pattern = re.escape(key).replace("_", r"[_\s-]*")
    heading = re.search(rf"(?im)^#+\s*{heading_key_pattern}\s*$", text)
    if not heading:
        return False
    tail = text[heading.end() :]
    body = re.split(r"(?m)^#+\s+", tail, maxsplit=1)[0]
    return _semantic_body_nonempty(_strip_html_comments(body).strip())


def _semantic_body_nonempty(body: str) -> bool:
    cleaned = html.unescape(_strip_html_tags(
        re.sub(r"(?m)^[ \t]*#.*$", "", body)
    )).strip()
    if re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", cleaned):
        return False
    if not _semantic_scalar_nonempty(cleaned):
        return False
    lines = [line for line in cleaned.splitlines() if line.strip()]
    if lines and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*[ \t]*:", lines[0]):
        if all(
            re.fullmatch(r"[ \t]+[A-Za-z_][A-Za-z0-9_]*[ \t]*:.*", line)
            for line in lines[1:]
        ):
            return False
    return True


def _direct_nested_match(block: str, key: str) -> re.Match[str] | None:
    key_lines = list(
        re.finditer(
            r"(?m)^([ \t]*)([A-Za-z_][A-Za-z0-9_]*)[ \t]*:[ \t]*([^\n#]*)",
            block,
        )
    )
    if not key_lines:
        return None
    direct_indent = min(len(match.group(1).expandtabs(8)) for match in key_lines)
    for match in key_lines:
        if (
            match.group(2) == key
            and len(match.group(1).expandtabs(8)) == direct_indent
        ):
            return match
    return None


def _direct_nested_matches(block: str, key: str) -> list[re.Match[str]]:
    key_lines = list(
        re.finditer(
            r"(?m)^([ \t]*)([A-Za-z_][A-Za-z0-9_]*)[ \t]*:[ \t]*([^\n#]*)",
            block,
        )
    )
    if not key_lines:
        return []
    direct_indent = min(len(match.group(1).expandtabs(8)) for match in key_lines)
    return [
        match
        for match in key_lines
        if match.group(2) == key
        and len(match.group(1).expandtabs(8)) == direct_indent
    ]


def _direct_nested_present(block: str, key: str) -> bool:
    return _direct_nested_match(block, key) is not None


def _nested_field_nonempty(block: str, key: str) -> bool:
    match = _direct_nested_match(block, key)
    if match is None:
        return False
    if _semantic_scalar_nonempty(match.group(3)):
        return True
    tail = block[match.end() :]
    nested = re.split(
        r"(?m)^[ \t]*[A-Za-z_][A-Za-z0-9_]*[ \t]*:", tail, maxsplit=1
    )[0]
    return _semantic_body_nonempty(nested)


def _nested_list_values(block: str, key: str) -> list[str]:
    match = _direct_nested_match(block, key)
    if match is None:
        return []
    inline = match.group(3).strip()
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


def _validate(text: str, *, allow_legacy_read_only: bool) -> dict:
    text = _strip_fenced_blocks(_strip_html_comments(text))
    version, version_error = _schema_version(text)
    if version == 1 and not allow_legacy_read_only:
        version_error = version_error or "current validation requires schema_version: 2"
    required = REQUIRED_KEYS + (V2_REQUIRED_KEYS if version >= 2 else [])
    missing = [key for key in required if not _has_top_level_key(text, key)]
    empty_required = [
        key
        for key in required
        if key not in missing and not _top_level_field_nonempty(text, key)
    ]
    adversarial_errors = []
    sandbox_errors = []
    if version >= 2 and "sandbox" not in missing:
        block = _top_level_block(text, "sandbox")
        for key in SANDBOX_REQUIRED_KEYS:
            matches = _direct_nested_matches(block, key)
            if not matches:
                sandbox_errors.append(f"missing sandbox.{key}")
            elif len(matches) > 1:
                sandbox_errors.append(f"duplicate sandbox.{key}")
            elif not _nested_field_nonempty(block, key):
                sandbox_errors.append(f"empty sandbox.{key}")
    if version >= 2 and "adversarial_gate" not in missing:
        block = _top_level_block(text, "adversarial_gate")
        for key in ADVERSARIAL_REQUIRED_KEYS:
            matches = _direct_nested_matches(block, key)
            if not matches:
                adversarial_errors.append(f"missing adversarial_gate.{key}")
            elif len(matches) > 1:
                adversarial_errors.append(f"duplicate adversarial_gate.{key}")
            elif not _nested_field_nonempty(block, key):
                adversarial_errors.append(f"empty adversarial_gate.{key}")
        risk = _scalar_value(block, "risk").lower()
        decision = _scalar_value(block, "decision").lower()
        if risk not in {"high", "low"}:
            adversarial_errors.append("adversarial_gate.risk must be high or low")
        if decision not in {"required", "skipped"}:
            adversarial_errors.append("adversarial_gate.decision must be required or skipped")
        reason_match = _direct_nested_match(block, "reason")
        if reason_match is not None:
            reason_scalar = reason_match.group(3).strip().strip("'\"")
            if re.fullmatch(
                r"(?i:true|false|yes|no|on|off|[-+]?(?:\d+(?:\.\d*)?|\.\d+))",
                reason_scalar,
            ):
                adversarial_errors.append("empty adversarial_gate.reason")
        if risk == "high":
            if decision != "required":
                adversarial_errors.append("high-risk diff requires decision: required")
            for key in ADVERSARIAL_HIGH_RISK_KEYS:
                if not _direct_nested_present(block, key):
                    adversarial_errors.append(f"missing adversarial_gate.{key}")
                elif not _nested_field_nonempty(block, key):
                    adversarial_errors.append(f"empty adversarial_gate.{key}")
        if risk == "low" and decision != "skipped":
            adversarial_errors.append("low-risk diff must record decision: skipped")
    return {
        "ok": not version_error
        and not missing
        and not empty_required
        and not adversarial_errors
        and not sandbox_errors,
        "schema_version": version,
        "schema_version_error": version_error,
        "missing_keys": missing,
        "empty_keys": empty_required,
        "adversarial_errors": adversarial_errors,
        "sandbox_errors": sandbox_errors,
        "required_keys": required,
    }


def validate(text: str) -> dict:
    """Validate a current iteration contract.

    Version-1 contracts remain readable only through the explicitly named
    ``validate_legacy_read_only`` compatibility API; they cannot be promoted.
    """

    return _validate(text, allow_legacy_read_only=False)


def validate_legacy_read_only(text: str) -> dict:
    """Parse historical version-1 contracts without granting promotion."""

    return _validate(text, allow_legacy_read_only=True)


def _heading_present(text: str, key: str) -> bool:
    pattern = re.escape(key).replace("_", r"[\s_-]*")
    return bool(re.search(rf"(?im)^#+\s*{pattern}\s*$", text))


def validate_handoff(text: str, *, schema_version: int = 1) -> dict:
    text = _strip_html_comments(text)
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
    empty_metadata = [
        key
        for key in HANDOFF_METADATA
        if key not in missing_metadata and not _top_level_field_nonempty(text, key)
    ]
    return {
        "ok": not missing_metadata
        and not empty_metadata
        and not missing_headings
        and not empty_headings,
        "missing_metadata": missing_metadata,
        "empty_metadata": empty_metadata,
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
    if lowered in HIGH_RISK_FILENAMES:
        return True
    if p.name == "SKILL.md":
        return True
    if parts & HIGH_RISK_PARTS:
        return True
    if p.suffix.lower() in HIGH_RISK_SUFFIXES:
        return True
    if any(token in lowered for token in ("contract", "prompt", "schema", "workflow")):
        return True
    if p.suffix.lower() in LOW_RISK_DATA_SUFFIXES:
        # JSON is low risk only when it is plainly evidence/data. Root package
        # metadata and runtime/config trees are handled above.
        return False
    return p.suffix.lower() not in LOW_RISK_SUFFIXES


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_attestation_ok(receipt: dict) -> bool:
    import hashlib

    key_raw = os.environ.get("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", "").strip()
    if not key_raw:
        return False
    key_path = Path(key_raw).expanduser()
    try:
        key = key_path.read_bytes()
    except OSError:
        return False
    if len(key) < 32:
        return False
    supplied = str(receipt.get("attestation_hmac_sha256") or "")
    payload = {
        key: value
        for key, value in receipt.items()
        if key != "attestation_hmac_sha256"
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


def validate_gate_evidence(text: str, root: Path) -> dict:
    import hashlib

    block = _top_level_block(text, "adversarial_gate")
    evidence_raw = _scalar_value(block, "evidence_dir")
    evidence_dir = (root / evidence_raw).resolve()
    result: dict = {
        "ok": False,
        "evidence_dir": str(evidence_dir),
        "missing_files": [],
        "errors": [],
    }
    try:
        evidence_dir.relative_to(root.resolve())
    except ValueError:
        result["errors"].append("evidence_dir escapes repository root")
        return result
    missing = [name for name in GATE_EVIDENCE_FILES if not (evidence_dir / name).is_file()]
    result["missing_files"] = missing
    if missing:
        return result
    try:
        gate = json.loads((evidence_dir / "gate_result.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (evidence_dir / "agent_attack_manifest.json").read_text(encoding="utf-8")
        )
        final_output = json.loads(
            (evidence_dir / "final_agent_output.json").read_text(encoding="utf-8")
        )
        receipt = json.loads(
            (evidence_dir / "live_provider_receipt.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(f"invalid evidence JSON: {exc}")
        return result
    base = _scalar_value(block, "base")
    candidate = _scalar_value(block, "candidate")
    scope = _nested_list_values(block, "attack_scope")
    try:
        literal_scope = [f":(literal){path}" for path in scope]
        diff = _git(root, "diff", base, candidate, "--", *literal_scope)
    except RuntimeError as exc:
        result["errors"].append(str(exc))
        return result
    expected_diff_sha = hashlib.sha256(diff.encode()).hexdigest()
    prompt_sha = _sha256_file(evidence_dir / "prompt.md")
    final_output_sha = _sha256_file(evidence_dir / "final_agent_output.json")
    manifest_attacks = manifest.get("attacks")
    receipt_usage = receipt.get("usage") or {}
    receipt_checks = {
        "event": receipt.get("event") == "provider_turn_completed",
        "provider": receipt.get("provider") in {"codex", "cursor", "grok", "composer"},
        "thread_id": receipt.get("thread_id") == gate.get("provider_thread_id"),
        "base": receipt.get("base") == base,
        "candidate": receipt.get("candidate") == candidate,
        "diff_sha256": receipt.get("diff_sha256") == expected_diff_sha,
        "prompt_sha256": receipt.get("prompt_sha256") == prompt_sha,
        "final_output_sha256": receipt.get("final_output_sha256") == final_output_sha,
        "returncode": receipt.get("returncode") == 0,
        "started_at_utc": bool(str(receipt.get("started_at_utc") or "").strip()),
        "completed_at_utc": bool(str(receipt.get("completed_at_utc") or "").strip()),
        "input_tokens": int(receipt_usage.get("input_tokens") or 0) > 0,
        "output_tokens": int(receipt_usage.get("output_tokens") or 0) > 0,
        "command": "codex" in str(receipt.get("command") or "").lower(),
        "host_attestation": _receipt_attestation_ok(receipt),
    }
    checks = {
        "base": gate.get("base") == base,
        "candidate": gate.get("candidate") == candidate,
        "diff_sha256": gate.get("diff_sha256") == expected_diff_sha,
        "raw_output_sha256": gate.get("raw_output_sha256") == final_output_sha,
        "provider_thread_id": bool(str(gate.get("provider_thread_id") or "").strip()),
        "manifest_shape": isinstance(manifest_attacks, list),
        "nonempty_executed_corpus": isinstance(manifest_attacks, list)
        and len(manifest_attacks) > 0,
        "generated_attack_count": gate.get("generated_attack_count")
        == len(manifest_attacks or []),
        "executed_attack_count": int(gate.get("executed_attack_count") or -1)
        >= len(manifest.get("attacks") or []),
        "escaped_attack_count": gate.get("escaped_attack_count") == 0,
        "deterministic_exit_code": gate.get("deterministic_exit_code") == 0,
        "deterministic_command": bool(str(gate.get("deterministic_command") or "").strip()),
        "live_sandbox_status": (gate.get("live_sandbox") or {}).get("status") == "passed",
        "final_output_shape": isinstance(final_output, dict)
        and isinstance(final_output.get("attacks"), list),
        "manifest_matches_output": isinstance(final_output, dict)
        and final_output.get("attacks") == manifest_attacks,
        "provider_receipt": all(receipt_checks.values()),
    }
    result.update(
        {
            "checks": checks,
            "receipt_checks": receipt_checks,
            "diff_sha256": expected_diff_sha,
            "ok": all(checks.values()),
        }
    )
    return result


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
        "unexpected_in_attack_scope": [],
    }
    if not base or not candidate:
        result["error"] = "base and candidate are required for diff binding"
        return result
    commit_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
    if not commit_pattern.fullmatch(base) or not commit_pattern.fullmatch(candidate):
        result["error"] = "base and candidate must be immutable commit hashes"
        return result
    try:
        base_sha = _git(root, "rev-parse", f"{base}^{{commit}}").strip()
        candidate_sha = _git(root, "rev-parse", f"{candidate}^{{commit}}").strip()
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, candidate_sha],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if ancestry.returncode != 0:
            result["error"] = "candidate must descend from base"
            return result
        changed = {
            line.strip()
            for line in _git(root, "diff", "--name-only", base_sha, candidate_sha, "--").splitlines()
            if line.strip()
        }
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result
    missing = sorted(changed - declared_scope)
    unexpected = sorted(declared_scope - changed)
    high_risk_paths = sorted(path for path in changed if _path_is_high_risk(path))
    risk_conflict = declared_risk == "low" and bool(high_risk_paths)
    result.update(
        {
            "ok": not missing
            and not unexpected
            and not risk_conflict
            and bool(changed),
            "base_sha": base_sha,
            "candidate_sha": candidate_sha,
            "changed_paths": sorted(changed),
            "high_risk_paths": high_risk_paths,
            "missing_from_attack_scope": missing,
            "unexpected_in_attack_scope": unexpected,
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
        help="Deprecated compatibility alias; current schema is required by default.",
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
    if int(result.get("schema_version") or 0) == 2:
        diff_result = validate_diff_binding(text, Path(args.root).resolve())
        result["diff_binding"] = diff_result
        result["ok"] = bool(result["ok"] and diff_result.get("ok"))
        if _scalar_value(_top_level_block(text, "adversarial_gate"), "risk").lower() == "high":
            gate_evidence = validate_gate_evidence(text, Path(args.root).resolve())
            result["gate_evidence"] = gate_evidence
            result["ok"] = bool(result["ok"] and gate_evidence.get("ok"))
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
