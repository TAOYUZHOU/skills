#!/usr/bin/env python3
"""Validate sanitized HARP history replays and a combined lifecycle receipt."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import shlex
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
    r"(?:^|[\s\"'])(?:(?:/[A-Za-z0-9._-]+)+|[A-Za-z]:\\)"
)
SAFE_LABEL_RE = re.compile(r"generic-[a-z0-9-]{1,48}")
PROFILE_KEYS = {
    "schema_version",
    "replay_id",
    "archetype",
    "capture_mode",
    "authority",
    "sanitization",
    "source_provenance",
    "facts",
}
QUEUE_KEYS = {
    "queue_id",
    "status",
    "terminal_class",
    "exit_code",
    "attempts",
    "executor_result_status",
    "executor_next_action_present",
    "expected_output_count",
    "output_assessment",
    "result_review_verdict",
    "review_identity_present",
    "strategy_attempt_identity_present",
}
EVENT_KEYS = {
    "event_seq",
    "event_type",
    "queue_id",
    "verdict",
    "observation_identity_present",
    "review_identity_present",
    "launch_identity_present",
    "strategy_attempt_identity_present",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return _sha256(encoded)


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


def _key_error(value: Any, expected: set[str], label: str) -> str:
    if not isinstance(value, dict):
        return f"{label} must be an object"
    actual = set(value)
    if actual != expected:
        return (
            f"{label} keys mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    return ""


def _profile_schema_errors(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    checks = [
        (profile, PROFILE_KEYS, "profile"),
        (profile.get("sanitization"), {
            "queue_id_pseudonyms",
            "absolute_paths_removed",
            "free_form_text_removed",
            "raw_database_copied",
            "prompt_or_agent_output_copied",
            "scientific_artifact_copied",
            "credentials_copied",
        }, "sanitization"),
        (profile.get("source_provenance"), {
            "state_files", "selected_event_digest", "selected_event_count"
        }, "source_provenance"),
        (profile.get("facts"), {
            "queue", "completion", "dag", "workflow_health", "review_events"
        }, "facts"),
    ]
    for value, expected, label in checks:
        error = _key_error(value, expected, label)
        if error:
            errors.append(error)
    facts = profile.get("facts") if isinstance(profile.get("facts"), dict) else {}
    for index, row in enumerate(facts.get("queue") or []):
        error = _key_error(row, QUEUE_KEYS, f"queue[{index}]")
        if error:
            errors.append(error)
            continue
        error = _key_error(
            row.get("output_assessment"),
            {"status", "missing_count", "checked_count"},
            f"queue[{index}].output_assessment",
        )
        if error:
            errors.append(error)
    for index, row in enumerate(facts.get("review_events") or []):
        error = _key_error(row, EVENT_KEYS, f"review_events[{index}]")
        if error:
            errors.append(error)
    completion = facts.get("completion")
    nested = [
        (completion, {
            "status", "complete", "blockers", "artifact_gate",
            "reviewer_acceptance", "active_plan_status_counts"
        }, "completion"),
        ((completion or {}).get("artifact_gate") if isinstance(completion, dict) else None,
         {"ok", "skipped", "missing_count"}, "completion.artifact_gate"),
        ((completion or {}).get("reviewer_acceptance") if isinstance(completion, dict) else None,
         {"ok", "required_count", "accepted_count", "rows"},
         "completion.reviewer_acceptance"),
        (facts.get("dag"), {"status", "frontier_count", "ready_count", "launchable_count"}, "dag"),
        (facts.get("workflow_health"), {
            "status", "severity", "active", "queue_counts", "dag_status", "issue_types"
        }, "workflow_health"),
    ]
    for value, expected, label in nested:
        error = _key_error(value, expected, label)
        if error:
            errors.append(error)
    reviewer = completion.get("reviewer_acceptance") if isinstance(completion, dict) else {}
    if isinstance(reviewer, dict):
        for index, row in enumerate(reviewer.get("rows") or []):
            error = _key_error(
                row,
                {"queue_id", "accepted", "review_identity_present", "strategy_attempt_identity_present"},
                f"completion.reviewer_acceptance.rows[{index}]",
            )
            if error:
                errors.append(error)
    provenance = profile.get("source_provenance")
    state_files = provenance.get("state_files") if isinstance(provenance, dict) else None
    error = _key_error(
        state_files,
        {"execution_queue.json", "completion_fact.json", "dag_state.json", "workflow_health_fact.json"},
        "source_provenance.state_files",
    )
    if error:
        errors.append(error)
    elif isinstance(state_files, dict):
        for name, value in state_files.items():
            error = _key_error(value, {"sha256", "size_bytes"}, f"state_files.{name}")
            if error:
                errors.append(error)
    return errors


def _host_attestation_ok(record: dict[str, Any]) -> bool:
    key_raw = os.environ.get("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", "").strip()
    if not key_raw:
        return False
    try:
        key = Path(key_raw).expanduser().read_bytes()
    except OSError:
        return False
    if len(key) < 32:
        return False
    supplied = str(record.get("attestation_hmac_sha256") or "")
    payload = {
        key_name: value
        for key_name, value in record.items()
        if key_name != "attestation_hmac_sha256"
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


def _pytest_command_ok(receipt: dict[str, Any]) -> bool:
    try:
        tokens = shlex.split(str(receipt.get("command") or ""))
    except ValueError:
        return False
    if tokens[:1] == ["pytest"]:
        body = tokens[1:]
    elif tokens[:3] in (["python3", "-m", "pytest"], ["python", "-m", "pytest"]):
        body = tokens[3:]
    else:
        return False
    test_path = str(receipt.get("test_path") or "")
    junit_path = str(receipt.get("junit_path") or "")
    required = [test_path, f"--junitxml={junit_path}"]
    remaining = list(body)
    for token in required:
        if remaining.count(token) != 1:
            return False
        remaining.remove(token)
    return all(token in {"-q"} for token in remaining)


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


def validate_replay_manifest(
    path: Path, *, require_host_attestation: bool = True
) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "path": path.name, "errors": [], "profiles": []}
    try:
        manifest = _load(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))
        return result
    if ABSOLUTE_PATH_RE.search(path.read_text(encoding="utf-8")):
        result["errors"].append("absolute path leaked in manifest")
    rows = manifest.get("profiles")
    manifest_error = _key_error(
        manifest,
        {
            "schema_version", "captured_at_utc", "capture_mode", "authority",
            "profile_count", "profiles", "attestation_hmac_sha256"
        },
        "manifest",
    )
    if manifest_error:
        result["errors"].append(manifest_error)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("capture_mode") != "read_only_whitelist"
        or manifest.get("authority") != "historical_observation_only"
        or manifest.get("profile_count") != 3
        or not str(manifest.get("captured_at_utc") or "").strip()
    ):
        result["errors"].append("manifest authority or capture metadata is invalid")
    if require_host_attestation and not _host_attestation_ok(manifest):
        result["errors"].append("manifest host attestation is invalid")
    if not isinstance(rows, list) or len(rows) != 3:
        result["errors"].append("manifest must contain exactly three profiles")
        return result
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            result["errors"].append("profile manifest row must be an object")
            continue
        row_error = _key_error(
            row, {"replay_id", "archetype", "path", "sha256"}, "manifest profile"
        )
        if row_error:
            result["errors"].append(row_error)
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
        if not isinstance(profile, dict):
            result["errors"].append(f"profile must be an object: {relative}")
            continue
        if _sha256(raw) != str(row.get("sha256") or ""):
            result["errors"].append(f"profile hash mismatch: {relative}")
        text = raw.decode("utf-8", errors="replace")
        if ABSOLUTE_PATH_RE.search(text):
            result["errors"].append(f"absolute path leaked: {relative}")
        result["errors"].extend(
            f"{relative}: {error}" for error in _profile_schema_errors(profile)
        )
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
        if any(
            int(value.get("size_bytes") or 0) <= 0
            for value in (provenance.get("state_files") or {}).values()
            if isinstance(value, dict)
        ):
            result["errors"].append(f"source provenance sizes are invalid: {relative}")
        events = (profile.get("facts") or {}).get("review_events") or []
        if (
            provenance.get("selected_event_digest") != _canonical_sha256(events)
            or provenance.get("selected_event_count") != len(events)
        ):
            result["errors"].append(f"selected event provenance mismatch: {relative}")
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
    result: dict[str, Any] = {"ok": False, "path": path.name, "errors": []}
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
    if not _pytest_command_ok(receipt):
        result["errors"].append("combined chain pytest command binding is invalid")
    if not re.fullmatch(
        r"[0-9a-f]{40}", str(receipt.get("candidate_revision") or "")
    ):
        result["errors"].append("combined chain candidate revision is invalid")
    if not str(receipt.get("test_path") or "").strip() or not re.fullmatch(
        r"[0-9a-f]{64}", str(receipt.get("test_sha256") or "")
    ):
        result["errors"].append("combined chain test binding is invalid")
    if not str(receipt.get("junit_path") or "").strip() or not re.fullmatch(
        r"[0-9a-f]{64}", str(receipt.get("junit_sha256") or "")
    ):
        result["errors"].append("combined chain JUnit binding is invalid")
    if receipt.get("boundary_mode") not in {
        "skill_gate_meta_validation",
        "target_local_real_producers_consumers",
    }:
        result["errors"].append("combined chain boundary mode is invalid")
    bindings = receipt.get("stage_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(CHAIN_STAGES):
        result["errors"].append("combined chain stage bindings are incomplete")
    else:
        for stage, binding in bindings.items():
            if (
                not isinstance(binding, dict)
                or set(binding) != {"producer", "consumer", "assertion"}
                or any(not str(value).strip() for value in binding.values())
            ):
                result["errors"].append(
                    f"combined chain stage binding is invalid: {stage}"
                )
                break
    if not _host_attestation_ok(receipt):
        result["errors"].append("combined chain host attestation is invalid")
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
