# Mechanic Dynamics: how the repo optimizes itself

The mechanic treats the repository as a plant that improves through a visible,
repeatable cycle. The "dynamics" are the rules of that cycle: what moves, what
is conserved, and what stops it.

## State as the center of gravity

`state.json` is the mechanic's single source of truth for iteration. It holds:

```json
{
  "schema_version": 1,
  "version": "0.1.0",
  "frontier": ["unfinished item", "known failure"],
  "history": [
    {
      "tick": 1,
      "hypothesis": "one bounded change",
      "diff_summary": "app.py: add validation",
      "evidence": ["evidence/20260806T000000Z.json"],
      "result": "verified" | "failed" | "blocked"
    }
  ],
  "budget": {"max_ticks": 20, "spent_ticks": 3},
  "converged": false
}
```

Only verified outcomes update the frontier. An observation that fails
verification becomes a recorded finding, not a silently dropped attempt.

## Conservation rules

- **Scope**: one hypothesis per tick; the contract bounds the total.
- **Evidence**: nothing moves the frontier without an evidence file hash-bound
  to the change.
- **History**: append-only; failed hypotheses are retained as data.
- **Rollback**: every tick is a git commit; revert is always possible.

## Optimization dynamics

Each tick maximizes information per token spent:

1. Prefer the smallest change that exercises the uncertain part of the
   frontier (test-first where cheap).
2. Prefer deleting or merging over adding new states/roles/compat paths.
3. When a hypothesis fails, distil the failure class into the next
   hypothesis instead of retrying the same change.
4. Batch cost control: run the app self-check and tests once per tick, reuse
   results across the record step.

## Checkpoints and human pause

After every N ticks (default 3) or when budget is exhausted, the mechanic
stops, summarizes frontier / evidence / next best hypothesis, and requests a
decision. A durable pause is a first-class outcome; it is not a failure, and it
must not be papered over by a "success" claim.

## Escalation

If the frontier crosses into promotion authority, releases, provider/queue
semantics, or cross-workspace recovery, the mechanic stops the light loop and
escalates to `delivery-alignment-iteration` (contracts, T-stages, external
verifiers, budget accounting).
