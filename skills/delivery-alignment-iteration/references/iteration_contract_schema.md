# Iteration Contract Schema

This reference defines a compact contract for preventing delivery mismatch.

## Required Fields

Use `schema_version: 2` for every new iteration contract. The checker continues
to accept legacy version-1 contracts so historical evidence remains readable.

- `intent`: The user's concrete desired outcome in one or two sentences.
- `non_goals`: Explicit exclusions. Use this to prevent adjacent substitutions.
- `ssot`: Sources of truth, such as docs, schemas, runtime facts, userprompt, or branches.
- `deliverables`: Files, artifacts, commits, branches, reports, or runtime states that must exist.
- `acceptance_criteria`: Observable conditions that make the work acceptable.
- `verification`: Commands or evidence checks used to verify acceptance.
- `traceability`: Mapping from acceptance criteria to deliverables and verification.
- `risks`: Residual risks, assumptions, or known gaps.
- `final_claims_allowed`: Claims the agent may make if verification passes.
- `handoff`: Stable docs path and update policy for the iteration handoff SSOT.
- `adversarial_gate`: Diff risk, gate decision, reason, immutable base,
  attack scope, and durable evidence directory.

Required for every iteration:

- `sandbox`: Atomic live-provider boundary check (role, fixture, invoke command,
  assertions, raw output and receipt paths). Dry-run evidence is supplementary
  and cannot satisfy completion.

For `adversarial_gate`:

- `risk: high` and `decision: required` are mandatory for executable code, new
  modules, parsers, schemas, reducers, writers, state/role/provider edges,
  queue/lease identity, process lifecycle, retry/resume, completion,
  projection, security, or release behavior.
- `risk: low` and `decision: skipped` are allowed for documentation, comments,
  static assets, or evidence-only changes only when the reason explains why no
  authoritative runtime behavior changes.
- High-risk contracts also declare immutable `base` and `candidate` commits,
  exact `attack_scope`, and `evidence_dir`.
  Before completion, the handoff records the real Agent invocation, raw output,
  attack manifest, deterministic commands/results, and zero escaped attacks.

## Recommended Review Questions

1. Does every acceptance criterion map to at least one deliverable?
2. Does every final claim have verification evidence?
3. Did any fallback replace a requested deliverable without explicit approval?
4. Did any machine/runtime issue get mixed into a domain/scientific blocker?
5. Did the implementation update all truth-source docs that the design changed?
6. Did the iteration try subtraction first before adding a new role, state file, hook, schema, fallback, or repair lane?
7. Is there a successful real-provider atomic sandbox for this iteration, with
   raw prompt/output and deterministic downstream assertions? If not, is status
   correctly `partial` or `blocked` rather than `complete`?
8. Does the stable docs handoff match the current diff, verification evidence,
   blockers, and next action?
9. Did a real Agent derive attacks from the exact high-risk diff, and do its
   executable oracles plus the fixed regression corpus report zero escapes?

## Minimal Markdown Template

```markdown
# Iteration Contract

schema_version: 2

intent:

non_goals:

ssot:

deliverables:

acceptance_criteria:

verification:

traceability:

risks:

final_claims_allowed:

handoff:
  path: docs/harp_iteration_handoff.md
  policy: Update after every material implementation or verification step.

adversarial_gate:
  risk: high
  decision: required
  reason: This changes an executable state boundary.
  base: <immutable commit>
  candidate: <immutable commit>
  attack_scope:
    - path/to/changed_module.py
  evidence_dir: docs/evidence/<iteration>
```

## Handoff Document Schema

The checker accepts Markdown headings with these meanings:

- Intent
- Non-goals
- Current truth
- Current phase
- Completed changes
- Verification evidence
- Open blockers and risks
- Exact next action
- Final claims allowed now
- Adversarial gate evidence

Also include non-empty scalar metadata for `status`, `updated_at_utc`,
`iteration`, and `contract` near the document top.
