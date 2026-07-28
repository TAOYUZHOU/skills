# Iteration Contract Schema

This reference defines a compact contract for preventing delivery mismatch.

## Required Fields

Use strict YAML with `schema_version: 2` for every new iteration contract.
Duplicate keys, YAML nulls, and YAML/Markdown hybrid syntax fail closed. The
checker exposes a separate read-only compatibility API for historical
version-1 Markdown; it cannot authorize promotion.

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
- Every current contract declares immutable `base` and `candidate` commits,
  exact `attack_scope`, and `evidence_dir`, including low-risk skips.
  Before completion, the handoff records the real Agent invocation, raw output,
  attack manifest, deterministic commands/results, and zero escaped attacks.
  The provider receipt must carry a valid HMAC attestation from a key outside
  the candidate repository, supplied to the checker through
  `DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE`. The deterministic gate result requires
  a separate attestation with the same host trust root. Low-risk skips may keep
  the attack corpus empty, but still provide the live-sandbox evidence bundle.
  `current_output_attacks` must exactly match the latest Agent output, and every
  current attack ID must appear in the cumulative `attacks` regression corpus.
  Historical corpus entries may come from earlier exact candidates.

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

## Minimal YAML Template

```yaml
schema_version: 2

intent: State the concrete requested outcome.

non_goals:
  - State an explicit exclusion.

ssot:
  - path: docs/source-of-truth.md
    reason: Why this source is authoritative.

deliverables:
  - id: D1
    path: path/to/deliverable

acceptance_criteria:
  - id: A1
    description: Observable completion condition.

verification:
  - id: V1
    command_or_check: pytest -q

traceability:
  - acceptance: A1
    deliverables: [D1]
    verification: [V1]

risks:
  - Residual risk.

final_claims_allowed:
  - Claim allowed after V1 passes.

handoff:
  path: docs/harp_iteration_handoff.md
  policy: Update after every material implementation or verification step.

sandbox:
  scope: Changed boundary.
  fixture: Minimal live fixture.
  invoke: Real provider command.
  assert: Deterministic postcondition.
  record: Durable evidence path.

adversarial_gate:
  risk: high
  decision: required
  reason: This changes an executable state boundary.
  base: "0000000000000000000000000000000000000000"
  candidate: "1111111111111111111111111111111111111111"
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
