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
SAFE_TOKEN_RE = re.compile(r"[a-zA-Z0-9_.:-]{0,80}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return _sha256(encoded)


def _token(value: Any) -> str:
    raw = str(value or "")
    return raw if SAFE_TOKEN_RE.fullmatch(raw) else "unknown"


def _read_stable_json(path: Path, *, attempts: int = 5) -> tuple[dict[str, Any], dict[str, Any]]:
    for _ in range(attempts):
        first = path.read_bytes()
        second = path.read_bytes()
        if first != second:
            continue
        value = json.loads(first)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {path}")
        return value, {"sha256": _sha256(first), "size_bytes": len(first)}
    raise RuntimeError(f"could not obtain a stable read: {path}")


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
        "status": _token(item.get("status")),
        "terminal_class": _token(item.get("harp_terminal_class")),
        "exit_code": item.get("exit_code") if isinstance(item.get("exit_code"), int) else None,
        "attempts": int(item.get("attempts") or 0),
        "executor_result_status": _token(handoff.get("status")),
        "executor_next_action_present": bool(str(handoff.get("next_action") or "").strip()),
        "expected_output_count": len(expected),
        "output_assessment": {
            "status": _token(assessment.get("status")),
            "missing_count": len(assessment.get("missing") or []),
            "checked_count": len(assessment.get("checked") or []),
        },
        "result_review_verdict": _token(item.get("result_review_verdict")),
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
                    "event_type": _token(event_type),
                    "queue_id": queue_map[raw_queue_id],
                    "verdict": _token(payload.get("verdict")),
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
        "status": _token(completion.get("status")),
        "complete": completion.get("complete") is True,
        "blockers": sorted(_token(value) for value in completion.get("blockers") or []),
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
            _token(key): int(value)
            for key, value in sorted(
                (completion.get("active_plan_status_counts") or {}).items()
            )
            if isinstance(value, int)
        },
    }


def _workflow_fact(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": _token(workflow.get("status")),
        "severity": _token(workflow.get("severity")),
        "active": workflow.get("active") is True,
        "queue_counts": dict(sorted((workflow.get("queue_counts") or {}).items())),
        "dag_status": _token(workflow.get("dag_status")),
        "issue_types": sorted(
            _token(issue.get("type"))
            for issue in workflow.get("issues") or []
            if isinstance(issue, dict) and str(issue.get("type") or "")
        ),
    }


def _dag_fact(dag: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": _token(dag.get("status")),
        "frontier_count": len(dag.get("frontier_node_ids") or []),
        "ready_count": len(dag.get("ready_node_ids") or []),
        "launchable_count": len(dag.get("launchable_node_ids") or []),
    }


def _capture(label: str, archetype: str, workspace: Path) -> dict[str, Any]:
    state_dir = workspace / ".state"
    raw: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for name in STATE_FILES:
        raw[name], provenance[name] = _read_stable_json(state_dir / name)
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
    events = _review_events(state_dir, queue_map)
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
