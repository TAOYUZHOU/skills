---
name: repo-structure-auditor
description: Read-only repository structure auditor for GitHub/code repositories. Use when Codex needs to evaluate whether a repo's physical directory layout matches its intended architecture, detect framework placement drift, domain/layer organization problems, junk-drawer directories like utils/helpers/common/services/lib, and produce a scored remediation plan without moving or editing source files.
license: Complete terms in LICENSE.txt
---

# Repo Structure Auditor

## Core Rule

Audit only. Do not move, delete, rename, format, refactor, or edit source files. The output is a report and a remediation plan.

## Workflow

1. Identify the target repo root and whether it is a git repository.
2. Read project signals: `README*`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING*`, package manifests, build config, `docs/architecture*`, ADRs, and top-level tree.
3. Run the scanner:

```bash
python3 skills/repo-structure-auditor/scripts/structure_audit.py /path/to/repo
```

4. Apply two-layer detection:
   - Layer 1: candidate scan for stack conventions, layer/domain layout, and junk drawers.
   - Layer 2: context verification so small projects, documented mixed layouts, and framework-specific exceptions are not over-reported.
5. Read the generated Markdown report and JSON summary.
6. Present the user with the score, highest-impact findings, and a staged plan.

## Safety Boundary

- Write reports only under `.repo-structure-audit/` or a user-specified output directory.
- Never modify source code while using this skill.
- If the user asks for implementation, first ask them to choose findings. Then create a separate implementation plan with explicit file moves and verification gates.
- For non-git directories, be extra conservative: report only and recommend initializing git or copying the tree before any later migration.

## Finding Actions

Use these action labels:

- `MOVE_MODULE`: a file or module appears placed outside stack/framework conventions.
- `SPLIT_JUNK_DRAWER`: a generic directory has mixed responsibilities and enough files to create navigation/ownership cost.
- `ALIGN_DOMAIN_STRUCTURE`: domain/layer layout is inconsistent with the inferred or documented architecture.
- `ADD_STRUCTURE_DOC`: the layout may be intentional but lacks a short architecture note to make it enforceable.

## Scoring

Start at 10.0 and subtract:

- Critical: 2.0
- High: 1.2
- Medium: 0.6
- Low: 0.25

Clamp at 0. Every finding must include evidence, action, effort, confidence, and recommendation.

## References

Load `references/structure-rules.md` when interpreting scanner output or doing a manual pass. The rules are a lightweight, host-independent extraction of `ln-646-project-structure-auditor` concepts.
