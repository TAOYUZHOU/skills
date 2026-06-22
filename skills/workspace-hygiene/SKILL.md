---
name: workspace-hygiene
description: Safe cleanup and archival workflow for AI-collaboration workspaces, bloated project trees, generated artifacts, duplicate files, stale experiments, historical reports, and non-git directories. Use when Codex needs to audit, organize, archive, or propose deletion of clutter while preserving rollback paths; especially useful for directories that may or may not be git repositories.
---

# Workspace Hygiene

## Core Rule

Treat cleanup as a staged audit. Never permanently delete files in the first pass. Prefer scan-only reports, then archive, then delete only after explicit user approval.

## Workflow

1. Define target directory and scope.
2. Run `scripts/hygiene_scan.py` in scan mode.
3. Review the Markdown report and JSON manifest.
4. Classify candidates into:
   - safe generated artifacts
   - archive candidates
   - needs human review
   - do not touch
5. For git repositories, require a clean working tree or user approval before edits.
6. For non-git directories, require archive-first behavior and a manifest before moving anything.
7. Validate after cleanup with available tests, smoke checks, or at least a before/after tree summary.

## Quick Start

```bash
python3 /root/.agents/skills/workspace-hygiene/scripts/hygiene_scan.py \
  /path/to/workspace \
  --output-dir /path/to/reports
```

Use `--stale-days 30` for aggressive recent-project cleanup or `--stale-days 90` for conservative cleanup.

## Git Mode

If the target is a git repository:

- Capture `git status --porcelain`.
- Prefer a clean working tree before moving files.
- Run baseline tests when the project exposes an obvious test command.
- Use `git mv` or ordinary `mv` plus manifest for archives.
- Commit cleanup categories separately if the user asks to persist changes.

## Non-Git Mode

If the target is not a git repository:

- Do not assume rollback exists.
- Default to scan-only.
- If moving files, move to `.cleanup-archive/YYYY-MM-DD/` inside the target or to a user-specified archive root.
- Write a manifest with original path, archive path, size, mtime, and hash when feasible.
- Do not permanently delete files unless the user explicitly asks.

## Candidate Handling

- Safe generated artifacts: `.DS_Store`, `Thumbs.db`, `__pycache__`, `.ipynb_checkpoints`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, coverage/test reports, obvious build caches.
- Archive candidates: timestamped experiment folders, AI-agent residual folders, old reports, duplicated exports, old notebooks, scratch scripts, log-heavy run directories.
- Review required: raw data, model checkpoints, vendor files, literature, manually curated docs, environment files, public APIs, notebooks with unique outputs.
- Do not touch: `.git`, lockfiles, source files, manifests, datasets, and anything named as canonical input unless explicitly approved.

Load `references/categories.md` when the target contains scientific data, model outputs, or mixed code/data artifacts.

## Reporting

Always include:

- whether the target is git or non-git
- file and directory counts
- total size and largest paths
- duplicate groups
- cleanup candidates grouped by risk
- recommended next action
- exact report paths

For experiments, stop after report generation unless the user explicitly asks to archive or delete.
