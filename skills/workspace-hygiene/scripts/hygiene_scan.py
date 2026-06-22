#!/usr/bin/env python3
"""Scan a workspace for safe cleanup and archival candidates.

The script is intentionally read-only. It writes JSON and Markdown reports but
does not move or delete target files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
}

SAFE_DIR_NAMES = {
    "__pycache__",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "htmlcov",
    "coverage",
    "test-results",
    "playwright-report",
}

BUILD_DIR_NAMES = {
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    ".vite",
    ".turbo",
    ".parcel-cache",
}

SAFE_FILE_NAMES = {".DS_Store", "Thumbs.db", "Desktop.ini"}
TEMP_SUFFIXES = (".tmp", ".temp", ".bak", ".backup", ".old", ".orig", ".swp", ".swo")
AI_HISTORY_MARKERS = (
    "add_by_",
    "harp",
    "scope_violation",
    "residual",
    "scratch",
    "tmp",
    "debug",
    "audit",
    "preflight",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a workspace for cleanup candidates.")
    parser.add_argument("target", type=Path, help="Directory to scan")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for reports")
    parser.add_argument("--stale-days", type=int, default=60, help="Age threshold for stale candidates")
    parser.add_argument("--large-mb", type=int, default=50, help="Large file threshold in MiB")
    parser.add_argument("--hash-limit-mb", type=int, default=64, help="Only hash files up to this size")
    parser.add_argument("--max-rows", type=int, default=80, help="Maximum rows per report section")
    return parser.parse_args()


def human_size(num: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{num} B"


def git_info(target: Path) -> dict[str, Any]:
    try:
        inside = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return {"is_git": False}
        root = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(target), "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        return {"is_git": True, "root": root, "dirty_entries": len(status)}
    except FileNotFoundError:
        return {"is_git": False, "git_available": False}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_candidate(
    candidates: list[dict[str, Any]],
    path: Path,
    target: Path,
    risk: str,
    reason: str,
    size: int | None,
    seen: set[tuple[str, str, str]],
) -> None:
    rel_path = str(path.relative_to(target))
    key = (rel_path, risk, reason)
    if key in seen:
        return
    seen.add(key)
    candidates.append(
        {
            "path": rel_path,
            "risk": risk,
            "reason": reason,
            "size": size,
        }
    )


def scan(target: Path, stale_days: int, large_mb: int, hash_limit_mb: int) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    stale_before = now - dt.timedelta(days=stale_days)
    large_bytes = large_mb * 1024 * 1024
    hash_limit = hash_limit_mb * 1024 * 1024

    files: list[dict[str, Any]] = []
    dirs: list[Path] = []
    candidates: list[dict[str, Any]] = []
    ext_counts: dict[str, int] = defaultdict(int)
    size_groups: dict[int, list[Path]] = defaultdict(list)
    total_size = 0
    errors: list[str] = []
    seen_candidates: set[tuple[str, str, str]] = set()

    for root, dirnames, filenames in os.walk(target):
        root_path = Path(root)
        kept_dirs = []
        for dirname in dirnames:
            child = root_path / dirname
            lower = dirname.lower()
            if dirname in SKIP_DIRS:
                continue
            dirs.append(child)
            if dirname in SAFE_DIR_NAMES:
                add_candidate(candidates, child, target, "safe-generated", f"generated/cache directory: {dirname}", None, seen_candidates)
            elif dirname in BUILD_DIR_NAMES:
                add_candidate(candidates, child, target, "safe-generated", f"build or report directory: {dirname}", None, seen_candidates)
            elif any(marker in lower for marker in AI_HISTORY_MARKERS):
                add_candidate(candidates, child, target, "archive-first", "AI/history/scratch marker in directory name", None, seen_candidates)
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            path = root_path / filename
            try:
                stat = path.stat()
            except OSError as exc:
                errors.append(f"{path}: {exc}")
                continue

            size = stat.st_size
            total_size += size
            suffix = path.suffix.lower() or "[no extension]"
            ext_counts[suffix] += 1
            mtime = dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
            rel = path.relative_to(target)
            lower_name = filename.lower()
            lower_parent = path.parent.name.lower()

            entry = {
                "path": str(rel),
                "size": size,
                "mtime": mtime.isoformat(),
                "suffix": suffix,
            }
            files.append(entry)
            size_groups[size].append(path)

            if filename in SAFE_FILE_NAMES or suffix in {".pyc", ".pyo"}:
                add_candidate(candidates, path, target, "safe-generated", "OS/editor/python generated file", size, seen_candidates)
            elif lower_name.endswith(TEMP_SUFFIXES) or lower_name.endswith("~"):
                add_candidate(candidates, path, target, "archive-first", "temporary or backup suffix", size, seen_candidates)
            elif any(marker in lower_name for marker in AI_HISTORY_MARKERS):
                add_candidate(candidates, path, target, "archive-first", "AI/history/scratch marker in file name", size, seen_candidates)
            elif lower_parent in {"smoke", "scratch", "debug", "tmp"}:
                add_candidate(candidates, path, target, "archive-first", f"file in {lower_parent} helper directory", size, seen_candidates)
            elif " (" in filename and ")" in filename:
                add_candidate(candidates, path, target, "archive-first", "versioned duplicate-looking filename", size, seen_candidates)

            if size >= large_bytes:
                add_candidate(candidates, path, target, "review", f"large file >= {large_mb} MiB", size, seen_candidates)
            if mtime < stale_before and suffix in {".md", ".log", ".txt", ".html"}:
                add_candidate(candidates, path, target, "review", f"stale {suffix} file older than {stale_days} days", size, seen_candidates)

    duplicate_groups = []
    for size, paths in size_groups.items():
        if size == 0 or len(paths) < 2 or size > hash_limit:
            continue
        hashes: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            try:
                hashes[sha256_file(path)].append(path)
            except OSError as exc:
                errors.append(f"{path}: {exc}")
        for digest, dup_paths in hashes.items():
            if len(dup_paths) > 1:
                duplicate_groups.append(
                    {
                        "sha256": digest,
                        "size": size,
                        "paths": [str(path.relative_to(target)) for path in dup_paths],
                    }
                )
                for path in dup_paths[1:]:
                    add_candidate(candidates, path, target, "archive-first", "exact duplicate by sha256", size, seen_candidates)

    return {
        "generated_at": now.isoformat(),
        "target": str(target),
        "git": git_info(target),
        "summary": {
            "file_count": len(files),
            "dir_count": len(dirs),
            "total_size": total_size,
            "total_size_human": human_size(total_size),
        },
        "extension_counts": dict(sorted(ext_counts.items(), key=lambda item: item[1], reverse=True)),
        "largest_files": sorted(files, key=lambda item: item["size"], reverse=True)[:50],
        "candidates": candidates,
        "duplicate_groups": duplicate_groups,
        "errors": errors,
    }


def candidate_summary(candidates: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "size": 0})
    for item in candidates:
        risk = item["risk"]
        out[risk]["count"] += 1
        if isinstance(item.get("size"), int):
            out[risk]["size"] += item["size"]
    return dict(out)


def write_markdown(report: dict[str, Any], path: Path, max_rows: int) -> None:
    summary = report["summary"]
    git = report["git"]
    cand_summary = candidate_summary(report["candidates"])

    lines = [
        "# Workspace Hygiene Report",
        "",
        f"- Target: `{report['target']}`",
        f"- Generated: `{report['generated_at']}`",
        f"- Git repository: `{git.get('is_git', False)}`",
    ]
    if git.get("is_git"):
        lines.append(f"- Git dirty entries: `{git.get('dirty_entries', 0)}`")
    else:
        lines.append("- Safety mode: `non-git scan-only; archive before delete`")
    lines.extend(
        [
            f"- Files: `{summary['file_count']}`",
            f"- Directories: `{summary['dir_count']}`",
            f"- Total size: `{summary['total_size_human']}`",
            "",
            "## Candidate Summary",
            "",
            "| Risk | Count | Known size |",
            "| --- | ---: | ---: |",
        ]
    )
    for risk in ["safe-generated", "archive-first", "review"]:
        item = cand_summary.get(risk, {"count": 0, "size": 0})
        lines.append(f"| {risk} | {item['count']} | {human_size(item['size'])} |")

    lines.extend(["", "## Largest Files", "", "| Size | Path |", "| ---: | --- |"])
    for item in report["largest_files"][:max_rows]:
        lines.append(f"| {human_size(item['size'])} | `{item['path']}` |")

    lines.extend(["", "## Cleanup Candidates", "", "| Risk | Size | Reason | Path |", "| --- | ---: | --- | --- |"])
    for item in report["candidates"][:max_rows]:
        size = human_size(item["size"]) if isinstance(item.get("size"), int) else ""
        lines.append(f"| {item['risk']} | {size} | {item['reason']} | `{item['path']}` |")

    lines.extend(["", "## Exact Duplicate Groups", ""])
    if report["duplicate_groups"]:
        for group in report["duplicate_groups"][:max_rows]:
            lines.append(f"- {human_size(group['size'])}, sha256 `{group['sha256'][:16]}...`")
            for dup_path in group["paths"]:
                lines.append(f"  - `{dup_path}`")
    else:
        lines.append("No exact duplicate groups found within hash limit.")

    lines.extend(["", "## Extension Counts", "", "| Extension | Count |", "| --- | ---: |"])
    for ext, count in list(report["extension_counts"].items())[:max_rows]:
        lines.append(f"| `{ext}` | {count} |")

    if report["errors"]:
        lines.extend(["", "## Scan Errors", ""])
        for error in report["errors"][:max_rows]:
            lines.append(f"- `{error}`")

    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            "Review `safe-generated` and `archive-first` candidates first. For non-git targets, archive with a manifest before any permanent deletion.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    target = args.target.expanduser().resolve()
    if not target.is_dir():
        raise SystemExit(f"Target is not a directory: {target}")

    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else target / ".cleanup-reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = scan(target, args.stale_days, args.large_mb, args.hash_limit_mb)
    json_path = output_dir / f"hygiene-report-{stamp}.json"
    md_path = output_dir / f"hygiene-report-{stamp}.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report, md_path, args.max_rows)

    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
