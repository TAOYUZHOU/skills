#!/usr/bin/env python3
"""Capture sanitized HARP control-state history from read-only workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARCHETYPES = {
    "review_projection_mismatch",
    "blocked_artifact_dependency",
    "partial_result_materialization",
}
STATE_FILES = (
    "execution_queue.json",
    "completion_fact.json",
    "dag_state.json",
    "workflow_health_fact.json",
)
EVENT_TYPES = ("ResultObservationRecorded", "ResultReviewRecorded")
SAFE_LABEL_RE = re.compile(r"generic-[a-z0-9-]{1,48}")
QUEUE_STATUSES = {"", "queued", "running", "done", "blocked", "superseded", "failed", "cancelled"}
QUEUE_COUNT_KEYS = {"queued", "running", "done", "blocked", "superseded", "failed"}
TERMINAL_CLASSES = {"", "success", "retryable_failure", "terminal_exception", "blocked", "cancelled"}
EXECUTOR_STATUSES = {"", "completed", "partial", "blocked", "failed"}
ASSESSMENT_STATUSES = {"", "passed", "missing", "no_contract", "semantic_only", "failed"}
REVIEW_VERDICTS = {"", "accepted", "blocked", "needs_improvement", "rejected"}
COMPLETION_STATUSES = {"", "not_ready", "complete", "blocked"}
WORKFLOW_STATUSES = {"", "healthy", "issues_detected"}
WORKFLOW_SEVERITIES = {"", "green", "yellow", "red"}
DAG_STATUSES = {"", "quiescent", "running", "blocked", "complete"}
COMPLETION_BLOCKERS = {
    "active_plan_nonterminal_rows_present",
    "artifact_gate_skipped",
    "execution_queue_blocked_items_present",
    "reviewer_acceptance_missing",
    "task_truth_update_needed",
}
WORKFLOW_ISSUES = {"COMPLETION_REFRESH_REQUIRED", "WORKFLOW_STALL"}
PLAN_STATUSES = {"pending", "running", "blocked", "completed", "failed", "unknown"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return _sha256(encoded)


def _enum(value: Any, allowed: set[str]) -> str:
    raw = str(value or "")
    return raw if raw in allowed else "unknown"


def _read_json_once(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    content = path.read_bytes()
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value, {"sha256": _sha256(content), "size_bytes": len(content)}


def _parse_source(raw: str) -> tuple[str, str, Path]:
    label, sep, rest = raw.partition("=")
    archetype, colon, path_raw = rest.partition(":")
    if not sep or not colon or not label.strip() or archetype not in ARCHETYPES:
        raise argparse.ArgumentTypeError(
            "source must be LABEL=ARCHETYPE:/absolute/workspace/path"
        )
    if not SAFE_LABEL_RE.fullmatch(label.strip()):
        raise argparse.ArgumentTypeError(
            "source label must be a generic pseudonym such as generic-review"
        )
    path = Path(path_raw).expanduser()
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("workspace source path must be absolute")
    return label.strip(), archetype, path


def _pseudonyms(items: list[dict[str, Any]]) -> dict[str, str]:
    ids = sorted(
        {
            str(item.get("id") or "").strip()
            for item in items
            if str(item.get("id") or "").strip()
        }
    )
    return {queue_id: f"q{index:03d}" for index, queue_id in enumerate(ids, 1)}


def _queue_fact(item: dict[str, Any], queue_id: str) -> dict[str, Any]:
    handoff = item.get("executor_handoff_result")
    handoff = handoff if isinstance(handoff, dict) else {}
    assessment = item.get("output_assessment")
    assessment = assessment if isinstance(assessment, dict) else {}
    expected = item.get("expected_outputs")
    expected = expected if isinstance(expected, list) else []
    return {
        "queue_id": queue_id,
        "status": _enum(item.get("status"), QUEUE_STATUSES),
        "terminal_class": _enum(item.get("harp_terminal_class"), TERMINAL_CLASSES),
        "exit_code": item.get("exit_code") if isinstance(item.get("exit_code"), int) else None,
        "attempts": int(item.get("attempts") or 0),
        "executor_result_status": _enum(handoff.get("status"), EXECUTOR_STATUSES),
        "executor_next_action_present": bool(str(handoff.get("next_action") or "").strip()),
        "expected_output_count": len(expected),
        "output_assessment": {
            "status": _enum(assessment.get("status"), ASSESSMENT_STATUSES),
            "missing_count": len(assessment.get("missing") or []),
            "checked_count": len(assessment.get("checked") or []),
        },
        "result_review_verdict": _enum(item.get("result_review_verdict"), REVIEW_VERDICTS),
        "review_identity_present": bool(
            str(item.get("last_result_review_identity") or "").strip()
        ),
        "strategy_attempt_identity_present": bool(
            str(item.get("strategy_attempt_id") or "").strip()
        ),
    }


def _review_events(state_dir: Path, queue_map: dict[str, str]) -> list[dict[str, Any]]:
    database = state_dir / "harp_state.sqlite3"
    if not database.is_file():
        return []
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    rows: list[dict[str, Any]] = []
    try:
        for seq, event_type, payload_json in connection.execute(
            "SELECT seq,event_type,payload_json FROM events "
            "WHERE event_type IN (?,?) ORDER BY seq",
            EVENT_TYPES,
        ):
            try:
                payload = json.loads(str(payload_json))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            raw_queue_id = str(
                payload.get("queue_id") or payload.get("parent_queue_id") or ""
            )
            if raw_queue_id not in queue_map:
                continue
            rows.append(
                {
                    "event_seq": int(seq),
                    "event_type": _enum(event_type, set(EVENT_TYPES)),
                    "queue_id": queue_map[raw_queue_id],
                    "verdict": _enum(payload.get("verdict"), REVIEW_VERDICTS),
                    "observation_identity_present": bool(
                        str(payload.get("observation_id") or "").strip()
                    ),
                    "review_identity_present": bool(
                        str(payload.get("review_identity") or "").strip()
                    ),
                    "launch_identity_present": bool(
                        str(payload.get("launch_token") or "").strip()
                    ),
                    "strategy_attempt_identity_present": bool(
                        str(payload.get("strategy_attempt_id") or "").strip()
                    ),
                }
            )
    finally:
        connection.close()
    return rows


def _completion_fact(
    completion: dict[str, Any], queue_map: dict[str, str]
) -> dict[str, Any]:
    reviewer = completion.get("reviewer_acceptance")
    reviewer = reviewer if isinstance(reviewer, dict) else {}
    rows = []
    for row in reviewer.get("rows") or []:
        if not isinstance(row, dict):
            continue
        raw_queue_id = str(row.get("queue_id") or "")
        rows.append(
            {
                "queue_id": queue_map.get(raw_queue_id, "external"),
                "accepted": row.get("accepted") is True,
                "review_identity_present": bool(
                    str(row.get("review_identity") or "").strip()
                ),
                "strategy_attempt_identity_present": bool(
                    str(row.get("strategy_attempt_id") or "").strip()
                ),
            }
        )
    artifact = completion.get("artifact_gate")
    artifact = artifact if isinstance(artifact, dict) else {}
    return {
        "status": _enum(completion.get("status"), COMPLETION_STATUSES),
        "complete": completion.get("complete") is True,
        "blockers": sorted(
            _enum(value, COMPLETION_BLOCKERS)
            for value in completion.get("blockers") or []
        ),
        "artifact_gate": {
            "ok": artifact.get("ok") is True,
            "skipped": artifact.get("skipped") is True,
            "missing_count": int(artifact.get("missing_count") or 0),
        },
        "reviewer_acceptance": {
            "ok": reviewer.get("ok") is True,
            "required_count": int(reviewer.get("required_count") or 0),
            "accepted_count": int(reviewer.get("accepted_count") or 0),
            "rows": rows,
        },
        "active_plan_status_counts": {
            _enum(key, PLAN_STATUSES): int(value)
            for key, value in sorted(
                (completion.get("active_plan_status_counts") or {}).items()
            )
            if isinstance(value, int)
        },
    }


def _workflow_fact(workflow: dict[str, Any]) -> dict[str, Any]:
    raw_counts = workflow.get("queue_counts") or {}
    raw_counts = raw_counts if isinstance(raw_counts, dict) else {}
    return {
        "status": _enum(workflow.get("status"), WORKFLOW_STATUSES),
        "severity": _enum(workflow.get("severity"), WORKFLOW_SEVERITIES),
        "active": workflow.get("active") is True,
        "queue_counts": {
            key: int(raw_counts.get(key) or 0)
            for key in sorted(QUEUE_COUNT_KEYS)
            if isinstance(raw_counts.get(key) or 0, int)
        },
        "dag_status": _enum(workflow.get("dag_status"), DAG_STATUSES),
        "issue_types": sorted(
            _enum(issue.get("type"), WORKFLOW_ISSUES)
            for issue in workflow.get("issues") or []
            if isinstance(issue, dict) and str(issue.get("type") or "")
        ),
    }


def _dag_fact(dag: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": _enum(dag.get("status"), DAG_STATUSES),
        "frontier_count": len(dag.get("frontier_node_ids") or []),
        "ready_count": len(dag.get("ready_node_ids") or []),
        "launchable_count": len(dag.get("launchable_node_ids") or []),
    }


def _snapshot(
    state_dir: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
]:
    raw: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for name in STATE_FILES:
        raw[name], provenance[name] = _read_json_once(state_dir / name)
    items = [
        item
        for item in raw["execution_queue.json"].get("items") or []
        if isinstance(item, dict)
    ]
    events = _review_events(state_dir, _pseudonyms(items))
    return raw, provenance, events


def _capture(
    label: str, archetype: str, workspace: Path, *, attempts: int = 5
) -> dict[str, Any]:
    state_dir = workspace / ".state"
    for _ in range(attempts):
        first = _snapshot(state_dir)
        second = _snapshot(state_dir)
        if first == second:
            raw, provenance, events = first
            break
    else:
        raise RuntimeError(f"could not obtain a stable cross-file snapshot: {state_dir}")
    items = [
        item
        for item in raw["execution_queue.json"].get("items") or []
        if isinstance(item, dict)
    ]
    queue_map = _pseudonyms(items)
    queue = [
        _queue_fact(item, queue_map[str(item.get("id") or "")])
        for item in items
        if str(item.get("id") or "") in queue_map
    ]
    return {
        "schema_version": 1,
        "replay_id": label,
        "archetype": archetype,
        "capture_mode": "read_only_whitelist",
        "authority": "historical_observation_only",
        "sanitization": {
            "queue_id_pseudonyms": True,
            "absolute_paths_removed": True,
            "free_form_text_removed": True,
            "raw_database_copied": False,
            "prompt_or_agent_output_copied": False,
            "scientific_artifact_copied": False,
            "credentials_copied": False,
        },
        "source_provenance": {
            "state_files": provenance,
            "selected_event_digest": _canonical_sha256(events),
            "selected_event_count": len(events),
        },
        "facts": {
            "queue": queue,
            "completion": _completion_fact(raw["completion_fact.json"], queue_map),
            "dag": _dag_fact(raw["dag_state.json"]),
            "workflow_health": _workflow_fact(raw["workflow_health_fact.json"]),
            "review_events": events,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        type=_parse_source,
        help="LABEL=ARCHETYPE:/absolute/workspace/path; repeat for each source",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sources: list[tuple[str, str, Path]] = args.source
    archetypes = [archetype for _label, archetype, _path in sources]
    if len(sources) != 3 or set(archetypes) != ARCHETYPES:
        parser.error("exactly three sources, one for each required archetype, are required")
    output_dir = args.output_dir.resolve()
    for _label, _archetype, workspace in sources:
        workspace_root = workspace.resolve()
        overlaps = False
        try:
            output_dir.relative_to(workspace_root)
        except ValueError:
            pass
        else:
            overlaps = True
        try:
            workspace_root.relative_to(output_dir)
        except ValueError:
            pass
        else:
            overlaps = True
        if overlaps:
            parser.error(
                "output-dir must not equal, contain, or descend from a historical source"
            )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    profiles = []
    for label, archetype, workspace in sources:
        profile = _capture(label, archetype, workspace)
        target = args.output_dir / f"{archetype}.json"
        target.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        profiles.append(
            {
                "replay_id": label,
                "archetype": archetype,
                "path": target.name,
                "sha256": _sha256(target.read_bytes()),
            }
        )
    manifest = {
        "schema_version": 1,
        "captured_at_utc": _utc_now(),
        "capture_mode": "read_only_whitelist",
        "authority": "historical_observation_only",
        "profile_count": len(profiles),
        "profiles": sorted(profiles, key=lambda row: row["archetype"]),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
