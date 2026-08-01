#!/usr/bin/env python3
"""Validate that an iteration contract contains the minimum alignment fields."""

from __future__ import annotations

import argparse
import html
import hmac
import importlib.util
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

LEGACY_REQUIRED_KEYS = [
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
REQUIRED_KEYS = [
    *LEGACY_REQUIRED_KEYS,
    "handoff",
]

V2_REQUIRED_KEYS = [
    "sandbox",
    "adversarial_gate",
    "combined_chain_gate",
    "historical_replay_gate",
]
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
HANDOFF_METADATA = ["status", "updated_at_utc", "iteration", "contract", "candidate"]
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
    ".svg",
    ".ts",
    ".tsx",
}
HIGH_RISK_PARTS = {
    ".github",
    "app",
    "bin",
    "config",
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
COMBINED_CHAIN_REQUIRED_KEYS = ["decision", "reason"]
COMBINED_CHAIN_EVIDENCE_KEYS = ["scope", "invoke", "assert", "evidence"]
HISTORICAL_REPLAY_REQUIRED_KEYS = ["decision", "reason"]
HISTORICAL_REPLAY_EVIDENCE_KEYS = [
    "fixture_manifest",
    "capture",
    "invoke",
    "assert",
    "evidence",
]
UNREACHABILITY_REQUIRED_KEYS = ["predicate", "invoke", "assert", "evidence"]
GATE_EVIDENCE_FILES = [
    "prompt.md",
    "final_agent_output.json",
    "agent_attack_manifest.json",
    "live_provider_receipt.json",
    "gate_result.json",
]


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


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
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        value = value[1:-1].strip()
    if value in {"", "''", '""', "~", "null", "Null", "NULL"}:
        return False
    if re.fullmatch(r"\[\s*\]|\{\s*\}", value):
        return False
    if re.fullmatch(r"[|>][-+]?[1-9]?", value):
        return False
    return True


def _strip_fenced_blocks(text: str) -> str:
    kept: list[str] = []
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        if not fence_char:
            opening = re.match(r"^[ ]{0,3}(`{3,}|~{3,})", line)
            if opening:
                fence = opening.group(1)
                fence_char = fence[0]
                fence_length = len(fence)
                continue
            kept.append(line)
            continue
        closing = re.match(
            rf"^[ ]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
            line,
        )
        if closing:
            fence_char = ""
            fence_length = 0
    return "".join(kept)


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
    cleaned = re.sub(r"!\[\s*\]\(\s*\)|\[\s*\]\(\s*\)", "", cleaned).strip()
    if not re.search(r"\w", cleaned, flags=re.UNICODE):
        return False
    if re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", cleaned):
        return False
    if re.fullmatch(r"[-*+]", cleaned):
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
    required = (
        LEGACY_REQUIRED_KEYS
        if version == 1 and allow_legacy_read_only
        else REQUIRED_KEYS + (V2_REQUIRED_KEYS if version >= 2 else [])
    )
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


def _load_v2_mapping(text: str) -> tuple[dict | None, str]:
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        return None, f"invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "version-2 contract must be a YAML mapping"
    return data, ""


def _structured_nonempty(value) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _conditional_gate_errors(
    data: dict,
    *,
    gate_name: str,
    high_risk: bool,
    required_keys: list[str],
    evidence_keys: list[str],
) -> list[str]:
    errors: list[str] = []
    if gate_name not in data:
        if high_risk:
            errors.append(f"missing {gate_name}")
        return errors
    gate = data.get(gate_name)
    if not isinstance(gate, dict):
        return [f"{gate_name} must be a mapping"]
    for key in required_keys:
        if key not in gate:
            errors.append(f"missing {gate_name}.{key}")
        elif not _structured_nonempty(gate[key]):
            errors.append(f"empty {gate_name}.{key}")
    decision = gate.get("decision")
    if decision not in {"required", "not_applicable"}:
        errors.append(f"{gate_name}.decision must be required or not_applicable")
    if decision == "required":
        for key in evidence_keys:
            if key not in gate:
                errors.append(f"missing {gate_name}.{key}")
            elif not _structured_nonempty(gate[key]):
                errors.append(f"empty {gate_name}.{key}")
    if decision == "not_applicable":
        proof = gate.get("unreachability")
        if not isinstance(proof, dict):
            errors.append(
                f"{gate_name}.unreachability must be a proof mapping when not_applicable"
            )
        else:
            for key in UNREACHABILITY_REQUIRED_KEYS:
                if key not in proof:
                    errors.append(f"missing {gate_name}.unreachability.{key}")
                elif not _structured_nonempty(proof[key]):
                    errors.append(f"empty {gate_name}.unreachability.{key}")
    return errors


def validate(text: str) -> dict:
    """Validate the strict YAML schema used by every current iteration."""

    data, parse_error = _load_v2_mapping(text)
    if data is None:
        return {
            "ok": False,
            "schema_version": 0,
            "schema_version_error": parse_error,
            "missing_keys": list(REQUIRED_KEYS + V2_REQUIRED_KEYS),
            "empty_keys": [],
            "adversarial_errors": [],
            "sandbox_errors": [],
            "combined_chain_errors": [],
            "historical_replay_errors": [],
            "required_keys": REQUIRED_KEYS + V2_REQUIRED_KEYS,
        }
    raw_version = re.findall(
        r"(?m)^schema_version[ \t]*:[ \t]*([^\n#]*)",
        text,
    )
    version = data.get("schema_version")
    if len(raw_version) != 1 or raw_version[0].strip() != "2":
        version_error = "invalid schema_version: expected literal integer 2"
    elif type(version) is not int or version != 2:
        version_error = "current validation requires integer schema_version: 2"
    else:
        version_error = ""
    required = REQUIRED_KEYS + V2_REQUIRED_KEYS
    missing = [key for key in required if key not in data]
    empty_required = [
        key
        for key in required
        if key in data and not _structured_nonempty(data[key])
    ]
    sandbox_errors: list[str] = []
    sandbox = data.get("sandbox")
    if "sandbox" in data:
        if not isinstance(sandbox, dict):
            sandbox_errors.extend(
                f"missing sandbox.{key}" for key in SANDBOX_REQUIRED_KEYS
            )
        else:
            for key in SANDBOX_REQUIRED_KEYS:
                if key not in sandbox:
                    sandbox_errors.append(f"missing sandbox.{key}")
                elif not _structured_nonempty(sandbox[key]):
                    sandbox_errors.append(f"empty sandbox.{key}")
    adversarial_errors: list[str] = []
    gate = data.get("adversarial_gate")
    if "adversarial_gate" in data:
        if not isinstance(gate, dict):
            adversarial_errors.extend(
                f"missing adversarial_gate.{key}"
                for key in ADVERSARIAL_REQUIRED_KEYS
            )
            gate = {}
        for key in ADVERSARIAL_REQUIRED_KEYS:
            if key not in gate:
                adversarial_errors.append(f"missing adversarial_gate.{key}")
            elif not _structured_nonempty(gate[key]):
                adversarial_errors.append(f"empty adversarial_gate.{key}")
        risk = gate.get("risk")
        decision = gate.get("decision")
        reason = gate.get("reason")
        if risk not in {"high", "low"}:
            adversarial_errors.append("adversarial_gate.risk must be high or low")
        if decision not in {"required", "skipped"}:
            adversarial_errors.append(
                "adversarial_gate.decision must be required or skipped"
            )
        if not isinstance(reason, str) or not reason.strip():
            marker = "empty adversarial_gate.reason"
            if marker not in adversarial_errors:
                adversarial_errors.append(marker)
        scope = gate.get("attack_scope")
        if not (
            isinstance(scope, list)
            and scope
            and all(isinstance(path, str) and path.strip() for path in scope)
        ):
            marker = "empty adversarial_gate.attack_scope"
            if marker not in adversarial_errors:
                adversarial_errors.append(marker)
        if risk == "high" and decision != "required":
            adversarial_errors.append("high-risk diff requires decision: required")
        if risk == "low" and decision != "skipped":
            adversarial_errors.append("low-risk diff must record decision: skipped")
    combined_chain_errors = _conditional_gate_errors(
        data,
        gate_name="combined_chain_gate",
        high_risk=True,
        required_keys=COMBINED_CHAIN_REQUIRED_KEYS,
        evidence_keys=COMBINED_CHAIN_EVIDENCE_KEYS,
    )
    historical_replay_errors = _conditional_gate_errors(
        data,
        gate_name="historical_replay_gate",
        high_risk=True,
        required_keys=HISTORICAL_REPLAY_REQUIRED_KEYS,
        evidence_keys=HISTORICAL_REPLAY_EVIDENCE_KEYS,
    )
    return {
        "ok": not version_error
        and not missing
        and not empty_required
        and not adversarial_errors
        and not sandbox_errors
        and not combined_chain_errors
        and not historical_replay_errors,
        "schema_version": version if type(version) is int else 0,
        "schema_version_error": version_error,
        "missing_keys": missing,
        "empty_keys": empty_required,
        "adversarial_errors": adversarial_errors,
        "sandbox_errors": sandbox_errors,
        "combined_chain_errors": combined_chain_errors,
        "historical_replay_errors": historical_replay_errors,
        "required_keys": required,
    }


def validate_legacy_read_only(text: str) -> dict:
    """Parse historical version-1 contracts without granting promotion."""

    return _validate(text, allow_legacy_read_only=True)


def _heading_present(text: str, key: str) -> bool:
    pattern = re.escape(key).replace("_", r"[\s_-]*")
    return bool(re.search(rf"(?im)^#+\s*{pattern}\s*$", text))


def _heading_nonempty(text: str, key: str) -> bool:
    pattern = re.escape(key).replace("_", r"[\s_-]*")
    heading = re.search(rf"(?im)^#+\s*{pattern}\s*$", text)
    if not heading:
        return False
    tail = text[heading.end() :]
    body = re.split(r"(?m)^#+\s+", tail, maxsplit=1)[0]
    return _semantic_body_nonempty(_strip_html_comments(body).strip())


def validate_handoff(text: str, *, schema_version: int = 1) -> dict:
    text = _strip_fenced_blocks(_strip_html_comments(text))
    missing_metadata = [key for key in HANDOFF_METADATA if not _has_top_level_key(text, key)]
    required_headings = HANDOFF_HEADINGS + (
        V2_HANDOFF_HEADINGS if schema_version >= 2 else []
    )
    missing_headings = [key for key in required_headings if not _heading_present(text, key)]
    empty_headings = [
        key
        for key in required_headings
        if key not in missing_headings and not _heading_nonempty(text, key)
    ]
    empty_metadata = [
        key
        for key in HANDOFF_METADATA
        if key not in missing_metadata and not _top_level_field_nonempty(text, key)
    ]
    status = _scalar_value(text, "status").lower()
    metadata_errors = []
    if status not in {"complete", "partial", "blocked"}:
        metadata_errors.append(
            "status must be complete, partial, or blocked"
        )
    return {
        "ok": not missing_metadata
        and not empty_metadata
        and not metadata_errors
        and not missing_headings
        and not empty_headings,
        "missing_metadata": missing_metadata,
        "empty_metadata": empty_metadata,
        "metadata_errors": metadata_errors,
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


def validate_expected_candidate(text: str, expected: str) -> dict:
    data, _ = _load_v2_mapping(text)
    gate = data.get("adversarial_gate") if data else None
    declared = gate.get("candidate") if isinstance(gate, dict) else ""
    risk = gate.get("risk") if isinstance(gate, dict) else ""
    if risk != "high":
        return {"ok": True, "declared": declared, "expected": expected}
    ok = bool(
        re.fullmatch(r"[0-9a-f]{40}", str(expected or ""))
        and declared == expected
    )
    return {
        "ok": ok,
        "declared": declared,
        "expected": expected,
        "error": "high-risk contract must match the externally frozen candidate"
        if not ok
        else "",
    }


def validate_handoff_candidate(
    contract_text: str, handoff_text: str, expected: str
) -> dict:
    """Bind the handoff's current candidate to the contract and trust-root input."""

    data, _ = _load_v2_mapping(contract_text)
    gate = data.get("adversarial_gate") if data else None
    contract_candidate = gate.get("candidate") if isinstance(gate, dict) else ""
    risk = gate.get("risk") if isinstance(gate, dict) else ""
    handoff_candidate = _scalar_value(
        _strip_fenced_blocks(_strip_html_comments(handoff_text)), "candidate"
    )
    checks = {
        "contract": bool(handoff_candidate)
        and handoff_candidate == contract_candidate,
        "external": risk != "high" or handoff_candidate == expected,
    }
    return {
        "ok": all(checks.values()),
        "handoff": handoff_candidate,
        "contract": contract_candidate,
        "expected": expected,
        "checks": checks,
        "error": "handoff candidate must match the contract and externally frozen candidate"
        if not all(checks.values())
        else "",
    }


def validate_handoff_binding(text: str, root: Path, supplied: Path) -> dict:
    data, _ = _load_v2_mapping(text)
    handoff = data.get("handoff") if data else None
    declared = handoff.get("path") if isinstance(handoff, dict) else ""
    if not declared:
        return {"ok": False, "error": "contract handoff.path is missing"}
    expected = (root.resolve() / declared).resolve()
    actual = supplied.resolve()
    docs_root = (root.resolve() / "docs").resolve()
    try:
        expected.relative_to(docs_root)
        contained = True
    except ValueError:
        contained = False
    return {
        "ok": expected == actual and contained,
        "declared": str(expected),
        "supplied": str(actual),
        "contained_in_docs": contained,
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
    if any(
        token in lowered
        for token in (
            "agent",
            "access",
            "auth",
            "contract",
            "control",
            "instruction",
            "permission",
            "policy",
            "prompt",
            "role",
            "runtime",
            "schema",
            "system",
            "workflow",
        )
    ):
        return True
    if p.suffix.lower() in LOW_RISK_DATA_SUFFIXES:
        # JSON is low risk only when it is plainly evidence/data. Root package
        # metadata and runtime/config trees are handled above.
        return False
    return p.suffix.lower() not in LOW_RISK_SUFFIXES


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _host_attestation_ok(record: dict) -> bool:
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
    supplied = str(record.get("attestation_hmac_sha256") or "")
    payload = {
        key: value
        for key, value in record.items()
        if key != "attestation_hmac_sha256"
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


def _contained_file(root: Path, raw: object, field: str) -> tuple[Path | None, str]:
    if not isinstance(raw, str) or not raw.strip():
        return None, f"{field} is missing"
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None, f"{field} escapes repository root"
    if not path.is_file():
        return None, f"{field} does not exist: {raw}"
    return path, ""


def _load_chain_validator():
    path = Path(__file__).with_name("validate_harp_chain_evidence.py")
    spec = importlib.util.spec_from_file_location(
        "delivery_alignment_chain_evidence", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load lifecycle evidence validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_unreachability(
    root: Path, gate_name: str, gate: dict, candidate: str
) -> tuple[bool, list[str], dict]:
    errors: list[str] = []
    proof = gate.get("unreachability")
    if not isinstance(proof, dict):
        return False, [f"{gate_name} lacks a structured unreachability proof"], {}
    evidence_path, error = _contained_file(
        root, proof.get("evidence"), f"{gate_name}.unreachability.evidence"
    )
    if error:
        errors.append(error)
        return False, errors, {}
    try:
        record = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"invalid {gate_name} unreachability evidence: {exc}"], {}
    predicate = proof.get("predicate")
    predicate_errors: list[str] = []
    observation: dict[str, str] = {}
    if not isinstance(predicate, dict) or set(predicate) != {"kind", "paths"}:
        predicate_errors.append(
            f"{gate_name} unreachability predicate must contain only kind and paths"
        )
    elif predicate.get("kind") != "all_paths_absent":
        predicate_errors.append(
            f"{gate_name} unreachability predicate kind is unsupported"
        )
    else:
        paths = predicate.get("paths")
        if not isinstance(paths, list) or not paths:
            predicate_errors.append(
                f"{gate_name} unreachability predicate paths must be nonempty"
            )
        elif not all(isinstance(path, str) for path in paths) or len(paths) != len(
            set(paths)
        ):
            predicate_errors.append(
                f"{gate_name} unreachability predicate paths must be unique strings"
            )
        else:
            resolved_root = root.resolve()
            for raw in paths:
                if (
                    not isinstance(raw, str)
                    or not raw.strip()
                    or raw != raw.strip()
                    or "\\" in raw
                    or Path(raw).is_absolute()
                    or any(part in {"", ".", ".."} for part in Path(raw).parts)
                ):
                    predicate_errors.append(
                        f"{gate_name} unreachability predicate path is unsafe: {raw!r}"
                    )
                    continue
                target = root / raw
                try:
                    target.resolve(strict=False).relative_to(resolved_root)
                except (OSError, ValueError):
                    predicate_errors.append(
                        f"{gate_name} unreachability predicate path escapes root: {raw}"
                    )
                    continue
                present = os.path.lexists(target)
                observation[raw] = "present" if present else "absent"
                if present:
                    predicate_errors.append(
                        f"{gate_name} unreachability predicate is false: {raw} is present"
                    )
    errors.extend(predicate_errors)
    expected = {
        "ok": True,
        "gate": gate_name,
        "reachable": False,
        "predicate": predicate,
        "observation": observation,
        "command": proof.get("invoke"),
        "assertion": proof.get("assert"),
        "candidate_revision": candidate,
        "repository_scope": "contract-root",
        "command_cwd": "contract-root",
    }
    if not isinstance(record, dict) or any(
        record.get(key) != value for key, value in expected.items()
    ):
        errors.append(f"{gate_name} unreachability evidence does not match its proof")
    if isinstance(record, dict) and not _host_attestation_ok(record):
        errors.append(f"{gate_name} unreachability host attestation is invalid")
    return not errors, errors, record if isinstance(record, dict) else {}


def _junit_matches_test(path: Path, test_path: str) -> bool:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return False
    cases = root.findall(".//testcase")
    if not cases:
        return False
    module = Path(test_path).with_suffix("").as_posix().replace("/", ".")
    if not any(
        str(case.get("classname") or "") == module
        or str(case.get("classname") or "").startswith(module + ".")
        for case in cases
    ):
        return False
    return not any(
        case.find(kind) is not None
        for case in cases
        for kind in ("failure", "error", "skipped")
    )


def validate_lifecycle_evidence(text: str, root: Path) -> dict:
    """Recompute required replay and combined-chain evidence fail-closed."""

    data, parse_error = _load_v2_mapping(text)
    result: dict = {
        "ok": False,
        "errors": [],
        "combined_chain": {"ok": True, "decision": "not_declared"},
        "historical_replay": {"ok": True, "decision": "not_declared"},
    }
    if data is None:
        result["errors"].append(parse_error)
        return result
    combined = data.get("combined_chain_gate")
    historical = data.get("historical_replay_gate")
    adversarial = data.get("adversarial_gate")
    candidate = (
        str(adversarial.get("candidate") or "")
        if isinstance(adversarial, dict)
        else ""
    )
    if not isinstance(combined, dict):
        result["errors"].append("combined_chain_gate is required")
    if not isinstance(historical, dict):
        result["errors"].append("historical_replay_gate is required")
    if result["errors"]:
        return result
    if not isinstance(combined, dict) and not isinstance(historical, dict):
        result["ok"] = True
        return result
    try:
        validator = _load_chain_validator()
    except Exception as exc:  # pragma: no cover - defensive import failure
        result["errors"].append(str(exc))
        return result

    replay_manifest: Path | None = None
    replay_validation: dict | None = None
    if isinstance(historical, dict):
        decision = historical.get("decision")
        result["historical_replay"] = {"ok": False, "decision": decision}
        if decision == "not_applicable":
            ok, errors, record = _validate_unreachability(
                root, "historical_replay_gate", historical, candidate
            )
            result["historical_replay"]["ok"] = ok
            result["historical_replay"]["proof"] = record
            result["errors"].extend(errors)
        elif decision == "required":
            replay_manifest, error = _contained_file(
                root,
                historical.get("fixture_manifest"),
                "historical_replay_gate.fixture_manifest",
            )
            evidence_path, evidence_error = _contained_file(
                root,
                historical.get("evidence"),
                "historical_replay_gate.evidence",
            )
            result["errors"].extend(
                value for value in (error, evidence_error) if value
            )
            if replay_manifest is not None:
                replay_validation = validator.validate_replay_manifest(replay_manifest)
                result["historical_replay"]["recomputed"] = replay_validation
                if replay_validation.get("ok") is not True:
                    result["errors"].append("historical replay manifest is invalid")
            if evidence_path is not None:
                try:
                    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    result["errors"].append(
                        f"invalid historical replay evidence JSON: {exc}"
                    )
                else:
                    stored_replay = stored.get("replay") if isinstance(stored, dict) else None
                    if (
                        not isinstance(stored, dict)
                        or stored.get("ok") is not True
                        or stored_replay != replay_validation
                    ):
                        result["errors"].append(
                            "historical replay evidence does not match recomputed validation"
                        )
            result["historical_replay"]["ok"] = bool(
                replay_validation
                and replay_validation.get("ok") is True
                and evidence_path is not None
                and not any("historical replay" in error for error in result["errors"])
            )

    if isinstance(combined, dict):
        decision = combined.get("decision")
        result["combined_chain"] = {"ok": False, "decision": decision}
        if decision == "not_applicable":
            ok, errors, record = _validate_unreachability(
                root, "combined_chain_gate", combined, candidate
            )
            result["combined_chain"]["ok"] = ok
            result["combined_chain"]["proof"] = record
            result["errors"].extend(errors)
        elif decision == "required":
            receipt, error = _contained_file(
                root,
                combined.get("evidence"),
                "combined_chain_gate.evidence",
            )
            if error:
                result["errors"].append(error)
            if replay_manifest is None:
                result["errors"].append(
                    "combined chain requires a required historical replay manifest"
                )
            if receipt is not None and replay_manifest is not None:
                try:
                    chain_validation = validator.validate_chain_receipt(
                        receipt, replay_manifest
                    )
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    chain_validation = {"ok": False, "errors": [str(exc)]}
                result["combined_chain"]["recomputed"] = chain_validation
                if chain_validation.get("ok") is not True:
                    result["errors"].append("combined chain receipt is invalid")
                try:
                    receipt_record = json.loads(receipt.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    receipt_record = {}
                test_path, test_error = _contained_file(
                    root,
                    receipt_record.get("test_path"),
                    "combined_chain_gate receipt test_path",
                )
                if test_error:
                    result["errors"].append(test_error)
                junit_path, junit_error = _contained_file(
                    root,
                    receipt_record.get("junit_path"),
                    "combined_chain_gate receipt junit_path",
                )
                if junit_error:
                    result["errors"].append(junit_error)
                binding_checks = {
                    "command": receipt_record.get("command") == combined.get("invoke"),
                    "pytest_command": validator._pytest_command_ok(receipt_record),
                    "candidate": receipt_record.get("candidate_revision")
                    == (data.get("adversarial_gate") or {}).get("candidate"),
                    "test_sha256": test_path is not None
                    and receipt_record.get("test_sha256") == _sha256_file(test_path),
                    "junit_sha256": junit_path is not None
                    and receipt_record.get("junit_sha256") == _sha256_file(junit_path),
                    "junit_test_result": junit_path is not None
                    and _junit_matches_test(
                        junit_path, str(receipt_record.get("test_path") or "")
                    ),
                }
                result["combined_chain"]["binding_checks"] = binding_checks
                if not all(binding_checks.values()):
                    result["errors"].append(
                        "combined chain receipt is not bound to contract, candidate, and test"
                    )
                result["combined_chain"]["ok"] = chain_validation.get("ok") is True

    result["ok"] = bool(
        not result["errors"]
        and result["combined_chain"].get("ok") is True
        and result["historical_replay"].get("ok") is True
    )
    return result


def validate_gate_evidence(text: str, root: Path) -> dict:
    import hashlib

    data, _ = _load_v2_mapping(text)
    gate_contract = data.get("adversarial_gate") if data else None
    if not isinstance(gate_contract, dict):
        return {
            "ok": False,
            "evidence_dir": "",
            "missing_files": [],
            "errors": ["adversarial_gate is not a mapping"],
        }
    evidence_raw = str(gate_contract.get("evidence_dir") or "")
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
    base = str(gate_contract.get("base") or "")
    candidate = str(gate_contract.get("candidate") or "")
    scope = list(gate_contract.get("attack_scope") or [])
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
    current_output_attacks = manifest.get("current_output_attacks")
    corpus_ids = {
        attack.get("id")
        for attack in (manifest_attacks or [])
        if isinstance(attack, dict) and attack.get("id")
    }
    current_ids = {
        attack.get("id")
        for attack in (current_output_attacks or [])
        if isinstance(attack, dict) and attack.get("id")
    }
    receipt_usage = receipt.get("usage") or {}
    risk = str(gate_contract.get("risk") or "").lower()
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
        "host_attestation": _host_attestation_ok(receipt),
    }
    checks = {
        "base": gate.get("base") == base,
        "candidate": gate.get("candidate") == candidate,
        "diff_sha256": gate.get("diff_sha256") == expected_diff_sha,
        "raw_output_sha256": gate.get("raw_output_sha256") == final_output_sha,
        "provider_thread_id": bool(str(gate.get("provider_thread_id") or "").strip()),
        "manifest_shape": isinstance(manifest_attacks, list),
        "nonempty_executed_corpus": risk != "high"
        or (isinstance(manifest_attacks, list) and len(manifest_attacks) > 0),
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
        "final_output_fingerprint": final_output.get("change_fingerprint")
        == expected_diff_sha,
        "manifest_matches_output": isinstance(current_output_attacks, list)
        and final_output.get("attacks") == current_output_attacks,
        "current_attacks_in_corpus": isinstance(manifest_attacks, list)
        and isinstance(current_output_attacks, list)
        and current_ids.issubset(corpus_ids),
        "gate_host_attestation": _host_attestation_ok(gate),
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
    data, _ = _load_v2_mapping(text)
    gate = data.get("adversarial_gate") if data else None
    if not isinstance(gate, dict):
        gate = {}
    declared_risk = str(gate.get("risk") or "").lower()
    base = str(gate.get("base") or "")
    candidate = str(gate.get("candidate") or "")
    declared_scope = set(gate.get("attack_scope") or [])
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
        summary = _git(root, "diff", "--summary", base_sha, candidate_sha, "--")
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result
    missing = sorted(changed - declared_scope)
    unexpected = sorted(declared_scope - changed)
    executable_mode_paths = {
        match.group(1)
        for match in re.finditer(
            r"(?m)^ mode change \d+ => 100755 (.+)$",
            summary,
        )
    }
    executable_mode_paths.update(
        match.group(1)
        for match in re.finditer(
            r"(?m)^ create mode 100755 (.+)$",
            summary,
        )
    )
    symlink_paths = set()
    gitlink_paths = set()
    for path in changed:
        for commit in (base_sha, candidate_sha):
            tree = _git(root, "ls-tree", commit, "--", path).strip()
            if tree.startswith("120000 "):
                symlink_paths.add(path)
                break
            if tree.startswith("160000 "):
                gitlink_paths.add(path)
                break
    high_risk_paths = sorted(
        path
        for path in changed
        if _path_is_high_risk(path)
        or path in executable_mode_paths
        or path in symlink_paths
        or path in gitlink_paths
    )
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
            "executable_mode_paths": sorted(executable_mode_paths),
            "symlink_paths": sorted(symlink_paths),
            "gitlink_paths": sorted(gitlink_paths),
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
        "--expected-candidate",
        default=os.environ.get("DELIVERY_ALIGNMENT_EXPECTED_CANDIDATE", ""),
        help="Externally frozen candidate SHA required for high-risk promotion.",
    )
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
        expected_candidate = validate_expected_candidate(
            text, args.expected_candidate
        )
        result["expected_candidate"] = expected_candidate
        result["ok"] = bool(result["ok"] and expected_candidate.get("ok"))
        handoff_candidate = validate_handoff_candidate(
            text, handoff_text if "handoff_text" in locals() else "", args.expected_candidate
        )
        result["handoff_candidate"] = handoff_candidate
        result["ok"] = bool(result["ok"] and handoff_candidate.get("ok"))
        lifecycle_evidence = validate_lifecycle_evidence(
            text, Path(args.root).resolve()
        )
        result["lifecycle_evidence"] = lifecycle_evidence
        result["ok"] = bool(result["ok"] and lifecycle_evidence.get("ok"))
        diff_result = validate_diff_binding(text, Path(args.root).resolve())
        result["diff_binding"] = diff_result
        result["ok"] = bool(result["ok"] and diff_result.get("ok"))
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
