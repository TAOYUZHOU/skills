"""Collect a read-only evidence bundle from a HARP workspace (Python 3.9+)."""
import argparse
import json
import sqlite3
import shutil
import tempfile
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_stamp(path):
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def read_attempts(database):
    # Opening the source directly can create SQLite sidecars even in mode=ro.
    files = (database, database.with_name(database.name + "-wal"))
    journal = database.with_name(database.name + "-journal")
    monitored = (*files, journal)
    before = [file_stamp(path) for path in monitored]
    if before[-1] is not None:
        raise ValueError("Rollback journal present; supply a consistent frozen database backup.")
    with tempfile.TemporaryDirectory(prefix="harp-run-atlas-") as directory:
        snapshot = Path(directory) / database.name
        for path, stamp in zip(files, before):
            if stamp is not None:
                shutil.copyfile(path, snapshot.with_name(path.name))
        if before != [file_stamp(path) for path in monitored]:
            raise ValueError("Database changed during copy; retry with a consistent frozen backup.")
        connection = sqlite3.connect(snapshot.as_uri() + "?mode=ro", uri=True)
        try:
            rows = connection.execute(
                "SELECT entity_id, state_json FROM entities "
                "WHERE entity_type = 'strategy_attempt' ORDER BY updated_seq"
            )
            return [{"id": key, "record": json.loads(state)} for key, state in rows]
        finally:
            connection.close()


def collect(workspace):
    state = workspace / ".state"
    active = state / "active_plan.json"
    plan_data = read_json(active) if active.is_file() else {}
    candidates = sorted((state / "executor_work_graph_candidates").glob("*.json"))
    if not candidates and (state / "executor_work_graph.json").is_file():
        candidates = [state / "executor_work_graph.json"]
    snapshots = []
    for path in candidates:
        payload = read_json(path)
        graph = payload.get("normalized_public_graph", payload)
        snapshots.append({
            "file": str(path.relative_to(workspace)),
            "graph_sha256": payload.get("graph_sha256"),
            "nodes": graph.get("nodes", []),
        })
    attempts = []
    observations = []
    database = state / "harp_state.sqlite3"
    if database.is_file():
        attempts = read_attempts(database)
    else:
        observations.append("No .state/harp_state.sqlite3 found. Check the run's state layout.")
    if not snapshots:
        observations.append("No executor work graph found. Recover explicit dependencies from other records.")
    if not snapshots and not plan_data and not attempts:
        raise ValueError("No supported run records found in " + str(workspace))
    return {
        "workspace": workspace.name,
        "sources": {"plans": str(active.relative_to(workspace)) if active.exists() else None,
                    "attempts": ".state/harp_state.sqlite3 / entities.strategy_attempt" if database.exists() else None},
        "snapshots": snapshots, "plans": plan_data, "attempts": attempts,
        "observations": observations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.workspace.resolve() in args.output.resolve().parents:
        parser.error("Write the analysis bundle outside the source workspace.")
    bundle = collect(args.workspace)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(bundle, output, ensure_ascii=False, indent=2)
        output.write("\n")
