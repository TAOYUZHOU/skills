#!/usr/bin/env python3
"""Read-only repository structure auditor.

Generates Markdown and JSON reports. It never edits, moves, deletes, or formats
files in the target repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from collections import Counter, defaultdict
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
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    "target",
    "vendor",
}

SOURCE_SUFFIXES = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
    ".rb",
    ".php",
    ".vue",
    ".svelte",
}

TEST_MARKERS = ("test", "tests", "__tests__", "spec", "fixture", "fixtures", "example", "examples")
GENERIC_DIRS = {"utils", "helpers", "common", "shared", "lib", "services", "misc"}
ROOT_ALLOWED = {
    "main.py",
    "manage.py",
    "setup.py",
    "conftest.py",
    "app.py",
    "index.ts",
    "index.js",
    "main.ts",
    "main.js",
    "server.ts",
    "server.js",
    "Program.cs",
    "main.go",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit repository structure without modifying code.")
    parser.add_argument("repo", type=Path, help="Repository or project directory")
    parser.add_argument("--output-dir", type=Path, default=None, help="Report output directory")
    parser.add_argument("--max-findings", type=int, default=80, help="Maximum findings to print in Markdown")
    return parser.parse_args()


def run_git(repo: Path, args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def git_info(repo: Path) -> dict[str, Any]:
    code, inside = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or inside != "true":
        return {"is_git": False}
    _, root = run_git(repo, ["rev-parse", "--show-toplevel"])
    _, branch = run_git(repo, ["branch", "--show-current"])
    _, status = run_git(repo, ["status", "--porcelain"])
    return {"is_git": True, "root": root, "branch": branch, "dirty_entries": len(status.splitlines()) if status else 0}


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def is_skipped_path(path: Path) -> bool:
    lower_parts = {part.lower() for part in path.parts}
    return any(part in lower_parts for part in TEST_MARKERS)


def classify_responsibility(name: str) -> str:
    lower = name.lower()
    if any(token in lower for token in ["date", "time", "format", "string", "text", "slug"]):
        return "formatting"
    if any(token in lower for token in ["http", "api", "client", "request", "fetch"]):
        return "io-client"
    if any(token in lower for token in ["db", "repo", "query", "sql", "model", "schema", "store"]):
        return "persistence"
    if any(token in lower for token in ["auth", "user", "session", "token"]):
        return "identity"
    if any(token in lower for token in ["component", "view", "page", "hook", "ui"]):
        return "ui"
    if any(token in lower for token in ["validate", "schema", "rule"]):
        return "validation"
    if any(token in lower for token in ["config", "env", "settings"]):
        return "configuration"
    return "general"


def detect_stack(root: Path, files: list[Path]) -> dict[str, Any]:
    names = {p.name for p in files}
    suffixes = Counter(p.suffix.lower() for p in files)
    stack: list[str] = []
    frameworks: list[str] = []

    if "package.json" in names:
        stack.append("javascript")
        pkg = root / "package.json"
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if any(dep in deps for dep in ["react", "next", "vite", "vue", "nuxt", "svelte", "@nestjs/core", "express"]):
                for key, label in [
                    ("react", "react"),
                    ("next", "next"),
                    ("vite", "vite"),
                    ("vue", "vue"),
                    ("nuxt", "nuxt"),
                    ("svelte", "svelte"),
                    ("@nestjs/core", "nestjs"),
                    ("express", "express"),
                ]:
                    if key in deps:
                        frameworks.append(label)
        except (OSError, json.JSONDecodeError):
            pass
    if any(name.startswith("tsconfig") for name in names) or suffixes[".ts"] or suffixes[".tsx"]:
        stack.append("typescript")
    if {"pyproject.toml", "setup.py", "requirements.txt", "uv.lock"} & names or suffixes[".py"]:
        stack.append("python")
    if "go.mod" in names or suffixes[".go"]:
        stack.append("go")
    if "Cargo.toml" in names or suffixes[".rs"]:
        stack.append("rust")
    if suffixes[".cs"]:
        stack.append("dotnet")
    if suffixes[".java"] or suffixes[".kt"]:
        stack.append("jvm")

    return {"languages": sorted(set(stack)), "frameworks": sorted(set(frameworks))}


def discover(root: Path) -> tuple[list[Path], list[Path], dict[Path, list[Path]]]:
    files: list[Path] = []
    dirs: list[Path] = []
    files_by_dir: dict[Path, list[Path]] = defaultdict(list)
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".repo-structure-audit")]
        for dirname in dirnames:
            dirs.append(current_path / dirname)
        for filename in filenames:
            path = current_path / filename
            files.append(path)
            files_by_dir[current_path].append(path)
    return files, dirs, files_by_dir


def has_architecture_docs(files: list[Path]) -> bool:
    for path in files:
        lower = str(path).lower()
        if any(token in lower for token in ["architecture", "adr", "decision", "design"]):
            if path.suffix.lower() in {".md", ".mdx", ".txt"}:
                return True
    return False


def add_finding(findings: list[dict[str, Any]], **item: Any) -> None:
    item.setdefault("confidence", "medium")
    item.setdefault("effort", "M")
    findings.append(item)


def audit(root: Path) -> dict[str, Any]:
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    files, dirs, files_by_dir = discover(root)
    source_files = [p for p in files if p.suffix.lower() in SOURCE_SUFFIXES and not is_skipped_path(p.relative_to(root))]
    stack = detect_stack(root, files)
    git = git_info(root)
    findings: list[dict[str, Any]] = []
    has_src = (root / "src").is_dir()
    has_docs = has_architecture_docs(files)

    root_source = [
        p
        for p in source_files
        if p.parent == root and p.name not in ROOT_ALLOWED and not p.name.startswith(".")
    ]
    if has_src and len(root_source) >= 3:
        add_finding(
            findings,
            action="MOVE_MODULE",
            severity="medium",
            confidence="high",
            effort="S",
            title="Move root-level implementation files into the source tree",
            evidence=[rel(p, root) for p in root_source[:10]],
            why="The repo already has a src/ layout, but implementation files remain at the root.",
            recommendation="Move these modules into src/ or a framework-specific app/package directory, updating imports in a separate implementation pass.",
            verification="Run the repo's import/typecheck/build command after moves.",
        )

    # Framework placement: UI components outside expected app/source dirs.
    if {"react", "next", "vite", "vue", "svelte"} & set(stack["frameworks"]):
        ui_files = [
            p
            for p in source_files
            if p.suffix.lower() in {".tsx", ".jsx", ".vue", ".svelte"}
            and not any(part in {"src", "app", "pages", "components", "packages", "apps"} for part in p.relative_to(root).parts[:-1])
        ]
        if len(ui_files) >= 2:
            add_finding(
                findings,
                action="MOVE_MODULE",
                severity="high",
                confidence="medium",
                effort="M",
                title="Align UI components with framework source conventions",
                evidence=[rel(p, root) for p in ui_files[:10]],
                why="Component files outside the app/source tree are harder for framework tooling and maintainers to locate.",
                recommendation="Group UI files under src/components, app, pages, packages, or apps according to the repo's dominant convention.",
                verification="Run the frontend build and route/component tests after a future move.",
            )

    # Python src/package layout.
    if "python" in stack["languages"]:
        py_root = [p for p in source_files if p.suffix == ".py" and p.parent == root and p.name not in ROOT_ALLOWED]
        package_dirs = [d for d in dirs if (d / "__init__.py").exists()]
        if len(py_root) >= 4 and package_dirs:
            add_finding(
                findings,
                action="MOVE_MODULE",
                severity="medium",
                confidence="medium",
                effort="M",
                title="Move Python modules out of the repository root",
                evidence=[rel(p, root) for p in py_root[:10]],
                why="Root-level Python modules coexist with package directories, which makes import boundaries and ownership less clear.",
                recommendation="Move reusable code into the existing package or a src/<package>/ layout; leave only CLI/bootstrap files at root.",
                verification="Run tests and import smoke checks after a future move.",
            )

    # Go layout.
    if "go" in stack["languages"]:
        go_root = [p for p in source_files if p.suffix == ".go" and p.parent == root and p.name != "main.go"]
        if len(go_root) >= 3 and not (root / "internal").exists():
            add_finding(
                findings,
                action="ALIGN_DOMAIN_STRUCTURE",
                severity="medium",
                confidence="medium",
                effort="M",
                title="Introduce clearer Go package boundaries",
                evidence=[rel(p, root) for p in go_root[:10]],
                why="Multiple root-level Go files without internal/ or package boundaries can blur binary, library, and private code responsibilities.",
                recommendation="Consider internal/ for private packages and cmd/ for binaries if the project is larger than a single command.",
                verification="Run go test ./... after any future package movement.",
            )

    # Junk drawers.
    for directory, dir_files in files_by_dir.items():
        name = directory.name.lower()
        if name not in GENERIC_DIRS:
            continue
        impl_files = [p for p in dir_files if p.suffix.lower() in SOURCE_SUFFIXES]
        if len(impl_files) <= 10:
            continue
        responsibilities = Counter(classify_responsibility(p.stem) for p in impl_files)
        mixed = [key for key, count in responsibilities.items() if count > 0 and key != "general"]
        if len(mixed) >= 3 or (len(impl_files) >= 20 and len(responsibilities) >= 3):
            severity = "high" if len(impl_files) >= 30 else "medium"
            add_finding(
                findings,
                action="SPLIT_JUNK_DRAWER",
                severity=severity,
                confidence="medium",
                effort="M" if len(impl_files) < 30 else "L",
                title=f"Split mixed-responsibility {rel(directory, root)} directory",
                evidence=[rel(p, root) for p in impl_files[:12]],
                why=f"`{rel(directory, root)}` contains {len(impl_files)} implementation files across responsibilities: {', '.join(sorted(responsibilities))}.",
                recommendation="Split by domain or responsibility, keeping pure helpers separate from IO, persistence, UI, and configuration glue.",
                verification="Run import/typecheck/tests after each small split in a future implementation pass.",
            )

    # Domain/layer consistency.
    src_roots = [root / name for name in ["src", "app", "packages", "apps"] if (root / name).is_dir()]
    layer_tokens = {
        "domain",
        "domains",
        "models",
        "entities",
        "application",
        "usecases",
        "use-cases",
        "services",
        "controllers",
        "routes",
        "handlers",
        "infrastructure",
        "repositories",
        "adapters",
    }
    layer_dirs = [d for d in dirs if d.name.lower() in layer_tokens and any(str(d).startswith(str(s)) for s in src_roots)]
    if src_roots and len(source_files) >= 40 and len(layer_dirs) < 2:
        add_finding(
            findings,
            action="ALIGN_DOMAIN_STRUCTURE",
            severity="low" if has_docs else "medium",
            confidence="low" if has_docs else "medium",
            effort="M",
            title="Clarify domain or layer structure for a growing source tree",
            evidence=[rel(s, root) for s in src_roots],
            why="The source tree is large enough that explicit domain/layer boundaries may reduce navigation and ownership cost.",
            recommendation="Document the intended module strategy, then align high-churn areas first. Do not force Clean Architecture if the project is intentionally simple.",
            verification="A future plan should add or update architecture docs before moving code.",
        )
    elif len(source_files) >= 40 and not has_docs:
        add_finding(
            findings,
            action="ADD_STRUCTURE_DOC",
            severity="low",
            confidence="high",
            effort="S",
            title="Add a short architecture note for the current layout",
            evidence=["README*/docs search did not find architecture, ADR, decision, or design notes"],
            why="A structure auditor can infer conventions, but maintainers and agents need an explicit source of truth to avoid repeated layout drift.",
            recommendation="Add docs/architecture.md or an ADR explaining the intended folder/module boundaries.",
            verification="Review that the doc names source roots, domains/layers, test placement, and exceptions.",
        )

    severity_cost = {"critical": 2.0, "high": 1.2, "medium": 0.6, "low": 0.25}
    score = 10.0 - sum(severity_cost.get(f["severity"], 0.6) for f in findings)
    score = max(0.0, round(score, 1))
    severity_counts = Counter(f["severity"] for f in findings)
    action_counts = Counter(f["action"] for f in findings)

    return {
        "generated_at": generated_at,
        "target": str(root),
        "git": git,
        "stack": stack,
        "summary": {
            "file_count": len(files),
            "dir_count": len(dirs),
            "source_file_count": len(source_files),
            "finding_count": len(findings),
            "score": score,
            "severity_counts": dict(severity_counts),
            "action_counts": dict(action_counts),
            "has_architecture_docs": has_docs,
        },
        "findings": findings,
    }


def write_markdown(report: dict[str, Any], path: Path, max_findings: int) -> None:
    summary = report["summary"]
    lines = [
        "# Repository Structure Audit",
        "",
        f"- Target: `{report['target']}`",
        f"- Generated: `{report['generated_at']}`",
        f"- Git repository: `{report['git'].get('is_git', False)}`",
        f"- Languages: `{', '.join(report['stack']['languages']) or 'unknown'}`",
        f"- Frameworks: `{', '.join(report['stack']['frameworks']) or 'none detected'}`",
        f"- Source files: `{summary['source_file_count']}`",
        f"- Findings: `{summary['finding_count']}`",
        f"- Score: `{summary['score']}/10`",
        "",
        "## Safety",
        "",
        "This audit is read-only. It proposes moves/splits/alignment work but did not modify source files.",
        "",
        "## Finding Summary",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for severity in ["critical", "high", "medium", "low"]:
        lines.append(f"| {severity} | {summary['severity_counts'].get(severity, 0)} |")
    lines.extend(["", "| Action | Count |", "| --- | ---: |"])
    for action, count in sorted(summary["action_counts"].items()):
        lines.append(f"| `{action}` | {count} |")

    lines.extend(["", "## Findings", ""])
    if not report["findings"]:
        lines.append("No structure findings detected by the lightweight scanner.")
    for index, finding in enumerate(report["findings"][:max_findings], start=1):
        lines.extend(
            [
                f"### {index}. {finding['title']}",
                "",
                f"- Action: `{finding['action']}`",
                f"- Severity: `{finding['severity']}`",
                f"- Confidence: `{finding['confidence']}`",
                f"- Effort: `{finding['effort']}`",
                f"- Why: {finding['why']}",
                f"- Recommendation: {finding['recommendation']}",
                f"- Future verification: `{finding['verification']}`",
                "- Evidence:",
            ]
        )
        for item in finding["evidence"]:
            lines.append(f"  - `{item}`")
        lines.append("")

    lines.extend(
        [
            "## Suggested Remediation Plan",
            "",
            "1. Review findings with high confidence first.",
            "2. Add or update architecture documentation if the intended structure is ambiguous.",
            "3. Implement one action at a time in a separate change: `ADD_STRUCTURE_DOC`, then `SPLIT_JUNK_DRAWER`, then `MOVE_MODULE` or `ALIGN_DOMAIN_STRUCTURE`.",
            "4. For each implementation batch, run the repo's tests, typecheck/build, and import checks.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")
    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else root / ".repo-structure-audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = audit(root)
    json_path = output_dir / f"structure-audit-{stamp}.json"
    md_path = output_dir / f"structure-audit-{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report, md_path, args.max_findings)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "score": report["summary"]["score"], "findings": report["summary"]["finding_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
