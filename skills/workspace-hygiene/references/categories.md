# Workspace Hygiene Categories

Use this reference when classifying cleanup candidates in AI-heavy research or engineering workspaces.

## Safe Generated Artifacts

Usually safe to remove or regenerate after review:

- `.DS_Store`, `Thumbs.db`, editor swap files
- `__pycache__/`, `*.pyc`, `.ipynb_checkpoints/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `coverage/`, `htmlcov/`, `test-results/`, `playwright-report/`
- build caches such as `dist/`, `build/`, `.next/`, `.vite/`, `.turbo/`

## Archive First

Move to archive before deletion:

- timestamped experiment runs
- AI-agent residual folders
- old status reports, summaries, temporary audit notes
- scratch scripts, ad hoc plotting scripts, debug utilities
- duplicated exports with version suffixes such as `(1)`, `(2)`, `copy`, `old`, `backup`
- notebooks whose outputs may still contain useful provenance

## Human Review

Require explicit confirmation:

- datasets, literature, vendor packages, model checkpoints
- environment files and credentials
- source files imported by other code
- lockfiles and package manifests
- manually curated documentation
- files used by external scripts, notebooks, or papers

## Non-Git Recovery Manifest

For non-git cleanup, record:

- original absolute path
- new archive path
- file size
- modified time
- sha256 for files small enough to hash
- reason for move
- timestamp of operation

No permanent delete should happen before the user has reviewed the manifest.
