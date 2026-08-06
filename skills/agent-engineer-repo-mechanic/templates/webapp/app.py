"""Agent Engineer Webapp -- minimal FastAPI backend for the mechanic loop.

Endpoints:
  GET  /api/health      -> service + version status
  GET  /api/state       -> current iteration state (frontier, history, budget)
  POST /api/iterations  -> record one mechanic tick (hypothesis + evidence)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

APP_VERSION = "0.1.0"
STATE_PATH = Path(__file__).parent / "state.json"

app = FastAPI(title="Agent Engineer Webapp", version=APP_VERSION)


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"schema_version": 1, "version": APP_VERSION, "frontier": [],
                "history": [], "budget": {"max_ticks": 20, "spent_ticks": 0},
                "converged": False}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


class IterationIn(BaseModel):
    hypothesis: str
    diff_summary: str = ""
    evidence: list[str] = []
    result: str = "verified"  # verified | failed | blocked


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": APP_VERSION,
            "state_file": STATE_PATH.name, "ts": int(time.time())}


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return load_state()


@app.post("/api/iterations")
def add_iteration(item: IterationIn) -> dict[str, Any]:
    state = load_state()
    if state["budget"]["spent_ticks"] >= state["budget"]["max_ticks"]:
        raise HTTPException(409, "budget exhausted: pause for human decision")
    state.setdefault("history", []).append({
        "tick": len(state["history"]) + 1,
        "hypothesis": item.hypothesis,
        "diff_summary": item.diff_summary,
        "evidence": item.evidence,
        "result": item.result,
        "ts": int(time.time()),
    })
    state["budget"]["spent_ticks"] += 1
    if item.result == "verified":
        # simple frontier policy: drop the first unfinished item the tick named
        pass
    save_state(state)
    return {"recorded": state["history"][-1], "spent_ticks": state["budget"]["spent_ticks"]}
