# Iteration Contract Schema

This reference defines a compact contract for preventing delivery mismatch.

## Required Fields

- `intent`: The user's concrete desired outcome in one or two sentences.
- `non_goals`: Explicit exclusions. Use this to prevent adjacent substitutions.
- `ssot`: Sources of truth, such as docs, schemas, runtime facts, userprompt, or branches.
- `deliverables`: Files, artifacts, commits, branches, reports, or runtime states that must exist.
- `acceptance_criteria`: Observable conditions that make the work acceptable.
- `verification`: Commands or evidence checks used to verify acceptance.
- `traceability`: Mapping from acceptance criteria to deliverables and verification.
- `risks`: Residual risks, assumptions, or known gaps.
- `final_claims_allowed`: Claims the agent may make if verification passes.

## Recommended Review Questions

1. Does every acceptance criterion map to at least one deliverable?
2. Does every final claim have verification evidence?
3. Did any fallback replace a requested deliverable without explicit approval?
4. Did any machine/runtime issue get mixed into a domain/scientific blocker?
5. Did the implementation update all truth-source docs that the design changed?
6. Did the iteration try subtraction first before adding a new role, state file, hook, schema, fallback, or repair lane?

## Minimal Markdown Template

```markdown
# Iteration Contract

intent:

non_goals:

ssot:

deliverables:

acceptance_criteria:

verification:

traceability:

risks:

final_claims_allowed:
```
