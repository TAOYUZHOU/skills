---
name: delivery-alignment-iteration
description: Use when planning, implementing, reviewing, or handing off a project iteration where the user cares about exact alignment between requested intent, acceptance criteria, implemented diff, tests, handoff state, and final claims; especially for HARP iterations, prior delivery mismatches, "货不对板", runtime repair work, docs, skills, prompt changes, release updates, or branch/workspace synchronization.
---

# Delivery Alignment Iteration

Use this skill to prevent implementation drift. The core output is a traceable contract plus one continuously maintained handoff SSOT: user intent -> acceptance criteria -> deliverables -> verification evidence -> current handoff -> final claims.

## Workflow

1. Restate the task as an iteration contract before editing nontrivial files.
2. Create or locate one stable handoff document under the target repository's
   `docs/` directory. For HARP, default to `docs/harp_iteration_handoff.md`.
   Record this path in the contract's `handoff.path`; this document is the SSOT
   for current iteration status and the next agent's starting point.
3. Identify the single sources of truth: user request, existing design docs, runtime facts, schemas, tests, and target branches.
4. Write deliverables and non-goals. If a requested deliverable is impossible or unsafe, state that before substituting anything.
5. Implement in small bounded changes. Do not silently replace the requested artifact with an adjacent artifact.
6. Update the handoff after every material implementation, verification, blocker,
   scope, or decision change. Do not postpone it until the final response.
7. Maintain a traceability matrix: each acceptance criterion must map to changed files and verification evidence.
8. Classify the candidate diff and apply the diff-directed adversarial gate
   below. For a high-risk diff, a real adversarial Agent must generate attacks
   from the actual diff; a static checklist, hand-written test list, or prompt
   inspection does not satisfy the gate.
9. Run at least one live atomic agent sandbox in every iteration — not only unit
   tests, mocks, or a full benchmark run. Spin up the smallest real slice (one
   role, one directive, or one handoff hop), invoke a real provider, and record
   the prompt, raw output, parsed result, downstream fact, and deterministic
   assertions. If no real provider can complete, the iteration cannot be marked
   `complete`; record it as `partial` or `blocked` with the exact provider
   evidence and next retry action. Architecture or role-boundary changes must
   exercise the changed boundary itself.
10. Run the contract and handoff checker when a contract file exists:

```bash
python3 scripts/check_delivery_contract.py \
  --contract /path/to/iteration_contract.yaml \
  --handoff /path/to/repo/docs/harp_iteration_handoff.md \
  --root /path/to/repo \
  --require-current-schema
```

11. Before the final response, reconcile the handoff against the actual diff and
    verification artifacts. Set `status` to `complete`, `partial`, or `blocked`,
    and leave one exact next action even when complete.
12. In the final response, only claim completed work that has evidence. Clearly separate completed, partial, blocked, and unverified items, and link the handoff.

## Required Contract Fields

Use YAML, Markdown, or another readable format, but include these fields:

```yaml
schema_version: 2
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
handoff:
  path: "docs/harp_iteration_handoff.md"
  policy: "Update after every material implementation or verification step."
adversarial_gate:
  risk: "high | low"
  decision: "required | skipped"
  reason: "Why the actual diff does or does not require a real adversarial Agent."
  base: "Immutable base commit for high-risk diffs."
  candidate: "Immutable candidate commit for high-risk diffs."
  attack_scope: ["Changed or new executable/protocol paths."]
  evidence_dir: "Durable prompt/output/attack/result directory."
```

## Handoff SSOT Contract

Use one stable file; do not create a new timestamped handoff on every turn. It
must contain:

- `status`, `updated_at_utc`, `iteration`, and the contract path;
- intent and non-goals;
- current truth sources and current phase;
- completed changes tied to real paths;
- verification commands, outcomes, and evidence paths;
- open blockers and residual risks;
- one exact next action;
- claims currently allowed by the evidence.

The handoff is current-state truth, not an append-only event log. Keep detailed
history in git, runtime ledgers, or evidence artifacts; update the handoff to
the latest reconciled state. Never mark a fix complete there before its mapped
verification passes.

## Diff-Directed Adversarial Gate

Classify a diff as `high` risk when it changes executable code, a new module, a
parser, schema, reducer, writer, state transition, provider or role edge, queue
or lease identity, process ownership, retry/resume logic, completion semantics,
projection, security boundary, or release behavior. Classify docs, comments,
static assets, and evidence-only changes as `low` unless they alter an
authoritative runtime contract. Record the decision and reason; do not infer
risk from file extension alone.

For every high-risk diff:

1. Freeze an immutable base and candidate commit plus the exact changed/new
   paths. Give a real adversarial Agent the bounded diff and only the adjacent
   contracts needed to understand the changed boundary.
2. Instruct the Agent to produce executable pytest cases or minimal repros with
   deterministic oracles. Include nonzero exits, missing returns, crash windows,
   stale identities, concurrent writers, malformed-but-schema-valid payloads,
   partial publication, and projection disagreement when relevant.
3. Isolate the Agent from the intended fix and expected answer. Permit it to
   write only tests, repros, manifests, and evidence—not product source.
4. For a bug fix, prove the frozen negative on the base and prevention on the
   candidate when safe. For a new module, use malicious inputs or mutation to
   prove that the generated test can fail for the defect it claims to detect.
5. Run both generated attacks and the fixed regression corpus. Completion
   requires zero escaped executable attacks. A prose finding without a
   deterministic oracle is review input, not a failed or passed attack.
6. Run the checker with `--require-current-schema`; current schema and exact
   diff checks are mandatory by default. It must prove
   every path in the exact `base..candidate` diff is in `attack_scope`.
7. Record the diff fingerprint, prompt, raw output, parsed attack manifest,
   executable artifacts, commands, exit codes, and escaped-attack count in the
   contract evidence directory and handoff. The checker must validate the
   evidence receipt against the pinned diff and require zero escapes. Sign the
   live-provider receipt with a host-controlled key outside the target
   repository and expose its path only to the trusted gate process through
   `DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE`; a candidate repository may not attest
   its own provider invocation. The trusted runner must attest both the provider
   receipt and the deterministic gate result; signing only the Agent turn does
   not prove that generated attacks were executed.

Low-risk diffs may set `decision: skipped`, but must still bind immutable
`base`, `candidate`, and complete `attack_scope`, and preserve a concrete reason.
If an Agent finds no attacks, record the successful invocation and empty
manifest; do not silently treat absence of output as success. The live atomic
sandbox remains independently required for every iteration, so this gate cannot
replace boundary validation.

## Alignment Rules

- Treat the user request and current truth-source docs as constraints, not inspiration.
- A fallback is not a delivery unless the contract explicitly accepts it.
- Apply Occam's razor before adding machinery: first try deletion, convergence, merge, downgrade, or deprecation of existing complex paths. Add a role, state file, hook, schema, fallback, or repair lane only when subtraction cannot satisfy the acceptance criteria, and explain why existing mechanisms were insufficient.
- A plan is not a fix; say "plan written" when only a plan was written.
- A final response is not a handoff substitute. If the handoff is absent or
  stale, the iteration is incomplete even when code and tests exist.
- Runtime protocol failures, environment failures, and scientific blockers must remain distinct.
- If the implementation changes the design, update the design doc and explain the consequence.
- If tests cannot run, record why and what evidence remains.
- Self-evolve is not exempt: every self-evolve candidate must use this skill,
  bind the adversarial evidence to its exact base/candidate identity, and pass
  the applicable gate before promotion or synchronization to the engine.

## Atomic Agent Sandbox Verification

Use this when the iteration touches agent roles, provider backends, prompt context, queue handoffs, structured directives, or cross-role message paths.

Goal: catch "tests green but architecture wrong" before a full workspace run.

Minimum sandbox shape:

```yaml
sandbox:
  scope: "one role or one handoff hop"
  fixture: "minimal workspace dir or tmp_path with only required .state files"
  invoke: "real provider when API/key available; otherwise dry-run prompt + deterministic scorer"
  assert:
    - "structured directive parses"
    - "downstream runtime fact matches expected shape"
    - "no cross-item prompt/output bleed under concurrency when relevant"
  record:
    - "prompt path"
    - "raw output path"
    - "pass/fail rubric scores"
```

Rules:

- Prefer an existing repo script when one already exists (for HARP: `scripts/evaluate_agent_boundary_from_history.py` with `--run-llm` for release/model/prompt changes).
- A dry-run may remain as supplementary diagnostic evidence, but it never
  satisfies iteration completion. Every iteration requires a successful real
  provider cell against the changed or most material boundary.
- Do not substitute a full AIRS/benchmark run for a missing atomic sandbox when the change is localized to one boundary.
- Add or extend a sandbox when subtracting over-engineered machinery, not only when adding new machinery.

## When To Read References

Read `references/iteration_contract_schema.md` when creating a durable contract, reviewing a mismatch, or adapting the schema for a repository.
