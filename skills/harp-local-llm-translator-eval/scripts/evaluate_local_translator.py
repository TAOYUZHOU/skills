#!/usr/bin/env python3
"""Evaluate a local small LLM as a HARP machine-code translator.

The script uses real HARP raw outputs, asks the local model for strict JSON,
then scores the translation against deterministic extraction of directive
markers and common IDs. It is intentionally generic: HARP-specific marker names
are protocol tokens, not task-domain assumptions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JSON_MARKERS = [
    "EXECUTOR_WORK_GRAPH_JSON",
    "PLAN_REQUEST_JSON",
    "PLAN_REVIEW_REASON_JSON",
    "COMPLETION_FACT_JSON",
    "RUN_SCORE_FACT_JSON",
    "REVIEWER_QUALITY_SCORE_JSON",
    "WORKLOAD_ESTIMATION_FACT_JSON",
    "INFORMATION_TRANSFER_FACT_JSON",
]

TEXT_MARKERS = [
    "PLAN_REVIEW",
    "REVIEW_VERDICT",
    "PLAN_REVIEW_REQUESTED",
    "COMPLETION_CLAIM",
    "GATE_REVIEW_REQUESTED",
]


@dataclass
class GpuSample:
    timestamp: float
    memory_used_mib: float | None
    utilization_gpu_pct: float | None
    power_draw_w: float | None


def _nvidia_smi_sample() -> GpuSample:
    cmd = [
        "nvidia-smi",
        "--query-gpu=memory.used,utilization.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=3)
    except Exception:
        return GpuSample(time.time(), None, None, None)
    line = out.strip().splitlines()[0] if out.strip() else ""
    parts = [p.strip() for p in line.split(",")]

    def parse_float(idx: int) -> float | None:
        try:
            return float(parts[idx])
        except Exception:
            return None

    return GpuSample(time.time(), parse_float(0), parse_float(1), parse_float(2))


class GpuPoller:
    def __init__(self, interval_s: float) -> None:
        self.interval_s = interval_s
        self.samples: list[GpuSample] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "GpuPoller":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.samples.append(_nvidia_smi_sample())
            self._stop.wait(self.interval_s)


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _json_after_marker(text: str, marker: str) -> list[Any]:
    decoder = json.JSONDecoder()
    results: list[Any] = []
    for match in re.finditer(rf"{re.escape(marker)}\s*=", text):
        start = match.end()
        while start < len(text) and text[start].isspace():
            start += 1
        try:
            obj, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        results.append(obj)
    return results


def _text_marker_values(text: str, marker: str) -> list[str]:
    values: list[str] = []
    for line in text.splitlines():
        if not re.match(rf"^{re.escape(marker)}(?:\s*=|$)", line):
            continue
        if "=" in line:
            values.append(line.split("=", 1)[1].strip())
        else:
            values.append(line.strip())
    return values


def deterministic_expectation(text: str) -> dict[str, Any]:
    directives: list[dict[str, Any]] = []
    ids: dict[str, list[str]] = {}
    for marker in JSON_MARKERS:
        for obj in _json_after_marker(text, marker):
            directive: dict[str, Any] = {"name": marker, "json_parseable": True}
            if isinstance(obj, dict):
                for key in ("plan_id", "graph_id", "subject_id", "review_mode", "status", "verdict"):
                    value = obj.get(key)
                    if isinstance(value, str):
                        directive[key] = value
                        ids.setdefault(key, []).append(value)
                nodes = obj.get("nodes")
                if isinstance(nodes, list):
                    directive["node_count"] = len(nodes)
            directives.append(directive)

    for marker in TEXT_MARKERS:
        for value in _text_marker_values(text, marker):
            directives.append({"name": marker, "value": value})
            if marker == "PLAN_REVIEW_REQUESTED" and value:
                ids.setdefault("plan_id", []).append(value)

    # Some structured_output_raw files are plain JSON without MARKER= prefix.
    if not directives:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            if isinstance(obj.get("nodes"), list):
                name = "EXECUTOR_WORK_GRAPH_JSON"
            elif obj.get("verdict") or obj.get("findings") or obj.get("minimum_revision"):
                name = "PLAN_REVIEW_REASON_JSON"
            else:
                name = "BARE_JSON"
            directive = {"name": name, "json_parseable": True}
            for key in ("plan_id", "graph_id", "authority", "status", "source"):
                value = obj.get(key)
                if isinstance(value, str):
                    directive[key] = value
                    ids.setdefault(key, []).append(value)
            nodes = obj.get("nodes")
            if isinstance(nodes, list):
                directive["node_count"] = len(nodes)
            directives.append(directive)

    return {
        "directive_count": len(directives),
        "directive_names": sorted({d["name"] for d in directives}),
        "directives": directives,
        "ids": {k: sorted(set(v)) for k, v in ids.items()},
    }


def build_prompt(path: Path, text: str, max_chars: int) -> list[dict[str, str]]:
    clipped = text[:max_chars]
    omitted = max(0, len(text) - len(clipped))
    system = (
        "You are a HARP machine-code translator. Convert raw agent output into "
        "a compact structured fact. Focus only on protocol/directive facts, not "
        "scientific judgement. Return strict JSON only."
    )
    user = {
        "source_file": str(path),
        "instructions": [
            "Extract directive markers such as EXECUTOR_WORK_GRAPH_JSON, PLAN_REQUEST_JSON, PLAN_REVIEW_REASON_JSON, PLAN_REVIEW, PLAN_REVIEW_REQUESTED, and bare JSON graph/review payloads.",
            "For each directive, report name, whether JSON is parseable, plan_id or graph_id if present, node_count if present, and a one-sentence protocol summary.",
            "Report accepted_changes as events that a runtime might need to emit, but mark uncertain items as needs_human_or_runtime_parser_check.",
            "Do not fabricate directives that are absent from the raw output.",
        ],
        "required_schema": {
            "schema_version": 1,
            "source_file": "string",
            "directives": [
                {
                    "name": "string",
                    "json_parseable": "boolean",
                    "plan_id": "string|null",
                    "graph_id": "string|null",
                    "node_count": "integer|null",
                    "summary": "string",
                }
            ],
            "accepted_changes": [
                {"event_type": "string", "subject_id": "string|null", "confidence": "high|medium|low"}
            ],
            "risk_flags": ["string"],
        },
        "raw_output_truncated_chars": omitted,
        "raw_output": clipped,
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]


def call_model(base_url: str, model: str, messages: list[dict[str, str]], max_tokens: int, timeout_s: int) -> dict[str, Any]:
    req_body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(req_body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.load(resp)


def parse_model_json(response: dict[str, Any]) -> tuple[dict[str, Any] | None, str, str | None]:
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {}) if isinstance(choice, dict) else {}
    content = message.get("content") or ""
    cleaned = _strip_code_fence(content)
    try:
        parsed = json.loads(cleaned)
    except Exception as exc:
        return None, content, f"{type(exc).__name__}: {exc}"
    return parsed, content, None


def score_translation(expected: dict[str, Any], parsed: dict[str, Any] | None) -> dict[str, Any]:
    if parsed is None:
        return {
            "parse_success": 0.0,
            "directive_recall": 0.0,
            "key_id_recall": 0.0,
            "fabrication_score": 0.0,
            "overall": 0.0,
            "reported_directive_names": [],
        }
    expected_names = set(expected.get("directive_names", []))
    reported_directives = parsed.get("directives", [])
    if not isinstance(reported_directives, list):
        reported_directives = []
    reported_names = {str(d.get("name")) for d in reported_directives if isinstance(d, dict) and d.get("name")}
    directive_recall = len(expected_names & reported_names) / len(expected_names) if expected_names else 1.0

    expected_ids = {str(v) for values in expected.get("ids", {}).values() for v in values}
    reported_blob = json.dumps(parsed, ensure_ascii=False)
    if expected_ids:
        key_id_recall = sum(1 for value in expected_ids if value in reported_blob) / len(expected_ids)
    else:
        key_id_recall = 1.0

    extra_names = reported_names - expected_names
    fabrication_score = max(0.0, 1.0 - (len(extra_names) / max(1, len(reported_names))))
    overall = 0.35 + 0.30 * directive_recall + 0.25 * key_id_recall + 0.10 * fabrication_score
    return {
        "parse_success": 1.0,
        "directive_recall": round(directive_recall, 4),
        "key_id_recall": round(key_id_recall, 4),
        "fabrication_score": round(fabrication_score, 4),
        "overall": round(overall, 4),
        "reported_directive_names": sorted(reported_names),
        "unexpected_directive_names": sorted(extra_names),
    }


def summarize_gpu(samples: list[GpuSample]) -> dict[str, Any]:
    def values(attr: str) -> list[float]:
        return [float(v) for s in samples if (v := getattr(s, attr)) is not None]

    result: dict[str, Any] = {"sample_count": len(samples)}
    for attr, out_name in [
        ("memory_used_mib", "memory_used_mib"),
        ("utilization_gpu_pct", "utilization_gpu_pct"),
        ("power_draw_w", "power_draw_w"),
    ]:
        vals = values(attr)
        if vals:
            result[out_name] = {
                "min": min(vals),
                "max": max(vals),
                "mean": round(statistics.fmean(vals), 3),
            }
    return result


def evaluate_file(args: argparse.Namespace, path: Path) -> dict[str, Any]:
    text = path.read_text(errors="replace")
    expected = deterministic_expectation(text)
    messages = build_prompt(path, text, args.max_chars)
    before = _nvidia_smi_sample()
    start = time.time()
    error = None
    response: dict[str, Any] | None = None
    with GpuPoller(args.poll_interval) as poller:
        try:
            response = call_model(args.base_url, args.model, messages, args.max_tokens, args.timeout)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, Exception) as exc:
            error = f"{type(exc).__name__}: {exc}"
    end = time.time()
    after = _nvidia_smi_sample()
    parsed = None
    raw_content = ""
    parse_error = None
    if response is not None:
        parsed, raw_content, parse_error = parse_model_json(response)
    score = score_translation(expected, parsed)
    return {
        "source_file": str(path),
        "sha256": hashlib.sha256(text.encode(errors="replace")).hexdigest(),
        "input_chars": len(text),
        "input_chars_sent": min(len(text), args.max_chars),
        "wall_seconds": round(end - start, 3),
        "request_error": error,
        "parse_error": parse_error,
        "expected": expected,
        "model_translation": parsed,
        "model_raw_content": raw_content[:5000],
        "score": score,
        "usage": (response or {}).get("usage"),
        "timings": (response or {}).get("timings"),
        "gpu": {
            "before": before.__dict__,
            "after": after.__dict__,
            "during": summarize_gpu(poller.samples),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="Raw HARP output file. May be repeated.")
    parser.add_argument("--out", required=True, help="JSON report path.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--model", default="qwythos-q4")
    parser.add_argument("--max-chars", type=int, default=18000)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    args = parser.parse_args()

    inputs = [Path(p) for p in args.input]
    missing = [str(p) for p in inputs if not p.exists()]
    if missing:
        raise SystemExit(f"Missing input files: {missing}")

    results = [evaluate_file(args, path) for path in inputs]
    scores = [r["score"]["overall"] for r in results]
    report = {
        "schema_version": 1,
        "base_url": args.base_url,
        "model": args.model,
        "generated_at_unix": time.time(),
        "summary": {
            "case_count": len(results),
            "mean_overall_score": round(statistics.fmean(scores), 4) if scores else None,
            "min_overall_score": min(scores) if scores else None,
            "all_parse_success": all(r["score"]["parse_success"] == 1.0 for r in results),
        },
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
