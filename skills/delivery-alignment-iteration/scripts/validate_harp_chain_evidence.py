#!/usr/bin/env python3
"""Validate sanitized HARP history replays and a combined lifecycle receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ARCHETYPES = {
    "review_projection_mismatch",
    "blocked_artifact_dependency",
    "partial_result_materialization",
}
CHAIN_STAGES = [
    "executor_handoff",
    "output_assessment",
    "result_review_admission",
    "result_observation_recorded",
    "result_review_recorded",
    "queue_terminal_projection",
    "artifact_gate",
    "completion_fact",
    "workflow_health_routing",
    "post_repair_health_audit",
]
ABSOLUTE_PATH_RE = re.compile(
    r"(?:^|[\s\"'])(?:/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+|[A-Za-z]:\\)"
)
SAFE_LABEL_RE = re.compile(r"generic-[a-z0-9-]{1,48}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _queue_by_id(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("queue_id") or ""): row
        for row in ((profile.get("facts") or {}).get("queue") or [])
        if isinstance(row, dict) and str(row.get("queue_id") or "")
    }


def _archetype_oracle(profile: dict[str, Any]) -> tuple[bool, list[str]]:
    archetype = str(profile.get("archetype") or "")
    facts = profile.get("facts") or {}
    queue = _queue_by_id(profile)
    completion = facts.get("completion") or {}
    events = facts.get("review_events") or []
    errors: list[str] = []
    if archetype == "review_projection_mismatch":
        accepted_done = {
            queue_id
            for queue_id, row in queue.items()
            if row.get("status") == "done"
            and row.get("result_review_verdict") == "accepted"
        }
        rejected_projection = {
            str(row.get("queue_id") or "")
            for row in ((completion.get("reviewer_acceptance") or {}).get("rows") or [])
            if isinstance(row, dict) and row.get("accepted") is False
        }
        missing_identity = {
            str(row.get("queue_id") or "")
            for row in events
            if isinstance(row, dict)
            and row.get("event_type") == "ResultReviewRecorded"
            and row.get("verdict") == "accepted"
            and row.get("review_identity_present") is False
        }
        if not (accepted_done & rejected_projection & missing_identity):
            errors.append("review/projection mismatch signature not reproduced")
    elif archetype == "blocked_artifact_dependency":
        missing = [
            row
            for row in queue.values()
            if row.get("status") == "blocked"
            and (row.get("output_assessment") or {}).get("status") == "missing"
        ]
        blockers = set(completion.get("blockers") or [])
        if not missing or "execution_queue_blocked_items_present" not in blockers:
            errors.append("blocked missing-artifact dependency signature not reproduced")
    elif archetype == "partial_result_materialization":
        partial = [
            row
            for row in queue.values()
            if row.get("executor_result_status") == "partial"
            and row.get("status") in {"done", "blocked"}
            and row.get("executor_next_action_present") is True
        ]
        if not partial or completion.get("complete") is True:
            errors.append("partial-result materialization signature not reproduced")
    else:
        errors.append(f"unknown archetype: {archetype}")
    return not errors, errors


def validate_replay_manifest(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "path": str(path), "errors": [], "profiles": []}
    try:
        manifest = _load(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))
        return result
    rows = manifest.get("profiles")
    if not isinstance(rows, list) or len(rows) != 3:
        result["errors"].append("manifest must contain exactly three profiles")
        return result
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            result["errors"].append("profile manifest row must be an object")
            continue
        archetype = str(row.get("archetype") or "")
        replay_id = str(row.get("replay_id") or "")
        relative = str(row.get("path") or "")
        if archetype in seen:
            result["errors"].append(f"duplicate archetype: {archetype}")
        seen.add(archetype)
        profile_path = (path.parent / relative).resolve()
        try:
            profile_path.relative_to(path.parent.resolve())
        except ValueError:
            result["errors"].append(f"profile escapes fixture directory: {relative}")
            continue
        try:
            raw = profile_path.read_bytes()
            profile = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            result["errors"].append(f"invalid profile {relative}: {exc}")
            continue
        if _sha256(raw) != str(row.get("sha256") or ""):
            result["errors"].append(f"profile hash mismatch: {relative}")
        text = raw.decode("utf-8", errors="replace")
        if ABSOLUTE_PATH_RE.search(text):
            result["errors"].append(f"absolute path leaked: {relative}")
        if profile.get("archetype") != archetype:
            result["errors"].append(f"manifest/profile archetype mismatch: {relative}")
        if profile.get("replay_id") != replay_id or not SAFE_LABEL_RE.fullmatch(
            replay_id
        ):
            result["errors"].append(f"invalid generic replay identity: {relative}")
        sanitization = profile.get("sanitization") or {}
        required_sanitization = {
            "queue_id_pseudonyms": True,
            "absolute_paths_removed": True,
            "free_form_text_removed": True,
            "raw_database_copied": False,
            "prompt_or_agent_output_copied": False,
            "scientific_artifact_copied": False,
            "credentials_copied": False,
        }
        if any(sanitization.get(key) is not value for key, value in required_sanitization.items()):
            result["errors"].append(f"sanitization contract mismatch: {relative}")
        provenance = profile.get("source_provenance") or {}
        digests = [
            str(value.get("sha256") or "")
            for value in (provenance.get("state_files") or {}).values()
            if isinstance(value, dict)
        ] + [str(provenance.get("selected_event_digest") or "")]
        if len(digests) != 5 or any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests):
            result["errors"].append(f"source provenance incomplete: {relative}")
        oracle_ok, oracle_errors = _archetype_oracle(profile)
        result["errors"].extend(f"{relative}: {error}" for error in oracle_errors)
        result["profiles"].append(
            {"archetype": archetype, "path": relative, "oracle_ok": oracle_ok}
        )
    if seen != ARCHETYPES:
        result["errors"].append(
            "archetypes must be exactly: " + ", ".join(sorted(ARCHETYPES))
        )
    result["ok"] = not result["errors"]
    return result


def validate_chain_receipt(path: Path, replay_manifest: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "path": str(path), "errors": []}
    try:
        receipt = _load(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))
        return result
    if receipt.get("status") != "passed" or receipt.get("exit_code") != 0:
        result["errors"].append("combined chain did not pass")
    if receipt.get("stages") != CHAIN_STAGES:
        result["errors"].append("combined chain stages are missing, duplicated, or reordered")
    if str(receipt.get("replay_manifest_sha256") or "") != _sha256(
        replay_manifest.read_bytes()
    ):
        result["errors"].append("combined chain is not bound to the replay manifest")
    replay_results = receipt.get("replay_results")
    if not isinstance(replay_results, list) or {
        str(row.get("archetype") or "")
        for row in replay_results
        if isinstance(row, dict)
    } != ARCHETYPES:
        result["errors"].append("combined chain must exercise all three replay archetypes")
    else:
        for row in replay_results:
            if not isinstance(row, dict) or not all(
                row.get(key) is True
                for key in (
                    "detected",
                    "owner_routed",
                    "review_required_when_applicable",
                    "premature_completion_rejected",
                    "later_health_audit_required",
                )
            ):
                result["errors"].append("a replay result lacks a required closure assertion")
                break
    happy = receipt.get("happy_path") or {}
    if not all(
        happy.get(key) is True
        for key in (
            "identity_preserved",
            "review_accepted",
            "artifact_gate_passed",
            "completion_true",
            "health_restored",
        )
    ) or happy.get("repeated_zero_work_wakeups") != 0:
        result["errors"].append("happy-path closure invariant failed")
    if not str(receipt.get("command") or "").strip():
        result["errors"].append("combined chain command is missing")
    result["ok"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-manifest", required=True, type=Path)
    parser.add_argument("--chain-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload: dict[str, Any] = {
        "replay": validate_replay_manifest(args.replay_manifest),
    }
    if args.chain_receipt:
        payload["combined_chain"] = validate_chain_receipt(
            args.chain_receipt, args.replay_manifest
        )
    payload["ok"] = all(
        value.get("ok") is True
        for key, value in payload.items()
        if key != "ok" and isinstance(value, dict)
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
