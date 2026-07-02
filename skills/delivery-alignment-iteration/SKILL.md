---
name: delivery-alignment-iteration
description: Use when planning, implementing, reviewing, or handing off a project iteration where the user cares about exact alignment between requested intent, acceptance criteria, implemented diff, tests, and final claims; especially after prior delivery mismatches, "货不对板", runtime repair work, docs, skills, prompt changes, release updates, or branch/workspace synchronization.
---

# Delivery Alignment Iteration

Use this skill to prevent implementation drift. The core output is a traceable contract: user intent -> acceptance criteria -> deliverables -> verification evidence -> final claims.

## Workflow

1. Restate the task as an iteration contract before editing nontrivial files.
2. Identify the single sources of truth: user request, existing design docs, runtime facts, schemas, tests, and target branches.
3. Write deliverables and non-goals. If a requested deliverable is impossible or unsafe, state that before substituting anything.
4. Implement in small bounded changes. Do not silently replace the requested artifact with an adjacent artifact.
5. Maintain a traceability matrix: each acceptance criterion must map to changed files and verification evidence.
6. Run the contract checker when a contract file exists:

```bash
python3 scripts/check_delivery_contract.py --contract /path/to/iteration_contract.yaml --root /path/to/repo
```

7. In the final response, only claim completed work that has evidence. Clearly separate completed, partial, blocked, and unverified items.

## Required Contract Fields

Use YAML, Markdown, or another readable format, but include these fields:

```yaml
intent: "What the user actually wants from this iteration."
non_goals:
  - "What this iteration explicitly will not do."
ssot:
  - path: "Path or source"
    reason: "Why it is authoritative"
deliverables:
  - id: D1
    path: "File, branch, workspace, or artifact"
    description: "What will exist when done"
acceptance_criteria:
  - id: A1
    description: "Observable condition for acceptance"
verification:
  - id: V1
    command_or_check: "Command, test, static check, or evidence review"
traceability:
  - acceptance: A1
    deliverables: [D1]
    verification: [V1]
risks:
  - "Known mismatch or residual risk"
final_claims_allowed:
  - "Claims that can be made if verification passes"
```

## Alignment Rules

- Treat the user request and current truth-source docs as constraints, not inspiration.
- A fallback is not a delivery unless the contract explicitly accepts it.
- A plan is not a fix; say "plan written" when only a plan was written.
- Runtime protocol failures, environment failures, and scientific blockers must remain distinct.
- If the implementation changes the design, update the design doc and explain the consequence.
- If tests cannot run, record why and what evidence remains.

## When To Read References

Read `references/iteration_contract_schema.md` when creating a durable contract, reviewing a mismatch, or adapting the schema for a repository.

