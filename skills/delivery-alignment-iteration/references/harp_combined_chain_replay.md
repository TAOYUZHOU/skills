# HARP Combined Lifecycle Chain and Historical Replay

Use this reference when an iteration can change queue, handoff, review,
artifact, completion, retry/resume, or workflow-health behavior. It defines two
additive gates: a target-local combined lifecycle-chain test and a sanitized
historical replay corpus. Neither gate replaces unit tests, regression tests,
the one-hop atomic sandbox, exact-diff adversarial testing, or a real-provider
cell when a provider boundary is reachable.

## Contents

- [Required Chain](#required-chain)
- [Three Historical Replay Archetypes](#three-historical-replay-archetypes)
- [Read-Only Capture and Sanitization](#read-only-capture-and-sanitization)
- [Evidence Contract](#evidence-contract)

## Required Chain

Exercise the real target-repository producers and consumers in this order:

1. `executor_handoff`
2. `output_assessment`
3. `result_review_admission`
4. `result_observation_recorded`
5. `result_review_recorded`
6. `queue_terminal_projection`
7. `artifact_gate`
8. `completion_fact`
9. `workflow_health_routing`
10. `post_repair_health_audit`

The test may use a temporary workspace, fake clock, and deterministic provider
adapter, but it must invoke the actual changed producers, event/reducer path,
projections, and downstream gate readers. Directly constructing the expected
terminal JSON, monkeypatching the consumer under test, or asserting only that
an intermediate event exists does not satisfy the gate.

At minimum, assert both directions:

- Happy path: handoff identity survives every hop, review is accepted by the
  completion consumer, required artifacts pass, completion becomes true,
  health becomes healthy, and later periodic audits do not emit repeated
  zero-work wakeups.
- Failure path: each replayed inconsistency is detected at its first
  authoritative consumer, routed to an explicit owner or typed pause, cannot
  produce premature completion, and remains eligible for a later health audit.

## Three Historical Replay Archetypes

Maintain exactly one sanitized profile for each archetype:

- `review_projection_mismatch`: a queue row is terminal and accepted while the
  completion projection rejects the same review because required identity was
  not preserved.
- `blocked_artifact_dependency`: expected outputs are missing, the queue is
  blocked, and completion carries the blocked-item dependency.
- `partial_result_materialization`: an executor reports `partial` with a next
  action while a downstream queue projection has already marked the item done
  or blocked; completion must remain false.

These profiles are regression inputs, not new control authorities. Their
oracle comes from the current target runtime contract plus the observed
inconsistency signature. A changed implementation may migrate the fixture
schema, but it may not weaken or silently discard the signature.

## Read-Only Capture and Sanitization

Capture historical source workspaces only with the bundled whitelist script:

```bash
python3 skills/delivery-alignment-iteration/scripts/capture_harp_history_replay.py \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --output-dir skills/delivery-alignment-iteration/assets/harp-history-replays
```

Before capture, resolve each workspace and record stable source-file hashes.
Open SQLite with `mode=ro` and `PRAGMA query_only=ON`; never run migrations,
runtime repair, queue mutation, or a provider against a historical source.
Read the complete JSON-plus-selected-event set twice and fail if any member or
event changes across the two snapshots. Reject an output directory equal to or
inside any historical source.

The durable fixture may contain only whitelisted booleans, enums, counts,
pseudonymous queue IDs, and provenance digests. Remove absolute paths, prompts,
free-form Agent output, scientific artifacts, credentials, raw database pages,
workspace names, and user data. Replay only from a copied fixture in an
isolated temporary directory. The replay must have no write handle to the
historical source.
After capture, the trusted runner outside the candidate repository signs the
manifest with its pre-provisioned trust root. A developer-selected temporary
key or unsigned manifest is diagnostic only and cannot authorize completion.
The same trusted run emits and separately signs `capture_receipt.json`, binding
the capture script hash, enforced read-only controls, all three source snapshot
digest sets, and each derived profile hash. The manifest names this receipt and
the iteration contract binds its path; a plausible synthetic manifest without
that capture witness is not acceptable provenance.

Replay oracles must preserve cross-field meaning, not merely enum shape. In the
blocked-artifact archetype, at least one blocked row must report
`output_assessment.status: missing`, a positive `missing_count`, and fewer
checked outputs than expected. A signed zero-missing row is not a blocked
artifact dependency.

## Evidence Contract

For an applicable high-risk iteration, the machine contract declares:

- `combined_chain_gate`: scope, invocation, ordered assertions, and durable
  receipt;
- `historical_replay_gate`: fixture manifest, read-only capture command,
  trusted capture receipt, replay invocation, archetype assertions, and durable
  validation evidence.

The combined receipt binds the contract invocation, immutable candidate,
target-local test path and SHA-256, fixture-manifest SHA-256, and a
producer/consumer/assertion triple for all ten stages. It records all three
archetype results and happy-path invariants, and has
a valid host-controlled HMAC attestation from outside the candidate repository. The
attested command must use the constrained pytest form, name the bound test path
as its only test target, and emit a hash-bound JUnit report. The checker must
find at least one testcase from that module and zero failures, errors, or skips;
a required target-local receipt binds one unique testcase to each of the ten
stage rows, and aggregate JUnit counters must also be green. A passing sibling
test plus an unrelated hashed chain test is invalid. Every row additionally
binds producer and consumer files from the immutable candidate tree and their
hashes. The constrained pytest invocation emits per-test coverage contexts;
each bound testcase must execute both files. A same-run causal trace binds the
ordered stages: producer output digest equals consumer input digest, and each
consumer output becomes the following stage input. Ten renamed `assert True`
tests or unrelated autouse calls cannot satisfy the chain. The trace is a
candidate artifact and is never authoritative by itself. The host runner must
also provide a signed call-boundary observer receipt from outside the candidate
tree. That observer records the canonical digest of the actual producer
argument and return plus the actual consumer argument and return, in event
order, and binds its tool hash, command, run ID, candidate, test, JUnit,
coverage, trace, and stage-binding hashes. The checker compares every claimed
trace value to those independently observed values; an internally consistent
candidate-generated hash chain is insufficient. The
`boundary_mode` must be `target_local_real_producers_consumers`;
`skill_gate_meta_validation` is diagnostic only and never satisfies a required
runtime gate. The
validator must fail closed for a missing stage, changed fixture hash, leaked
absolute path, missing source provenance, absent archetype, incomplete closure
assertion, or nonzero repeated zero-work wakeups.

If a gate is deterministically unreachable, use `decision: not_applicable` and
include an `unreachability` mapping with a declarative `predicate`, `invoke`,
`assert`, and a durable machine-readable, host-attested `evidence` record bound
to that oracle, frozen candidate, repository scope, and command working
directory. The checker re-evaluates the predicate in the current contract root.
For the combined gate, only the fixed `no_harp_runtime_boundaries` predicate is
accepted; an author-selected absent path is not enough. That predicate requires
a separately host-selected and signed scope-classification record outside the
candidate repository. The classification must bind the repository identity,
exact frozen base and candidate, binary diff digest, complete changed-path set,
and an independent assertion that no target HARP producer or consumer is added,
changed, or removed. A lexical scan can only contradict this classification;
it can never grant N/A on its own. The contradiction inventory unions lifecycle
signals from the complete immutable candidate tree, including across packages
and evidence directories, and reads base blobs for deletions. Mutable worktree
deletion cannot hide unchanged or removed runtime code. Signing a past observation does not
establish current unreachability. Cost, missing time, existing green
unit tests, or a one-hop mock is not an unreachability proof. A required gate
without passing evidence keeps the iteration `partial` or `blocked`.

Validate durable evidence with:

```bash
python3 skills/delivery-alignment-iteration/scripts/validate_harp_chain_evidence.py \
  --replay-manifest skills/delivery-alignment-iteration/assets/harp-history-replays/manifest.json \
  --chain-receipt docs/evidence/<iteration>/combined_chain_receipt.json
```

The promotion checker additionally receives the host records explicitly:

```bash
python3 skills/delivery-alignment-iteration/scripts/check_delivery_contract.py \
  --contract docs/iteration_contracts/<iteration>.yaml \
  --handoff docs/harp_iteration_handoff.md --root . \
  --expected-candidate <sha> \
  --expected-forward-patch-sha256 <sha256> \
  --scope-classification <outside-repo-signed-json> \
  --chain-observer-receipt <outside-repo-signed-json>
```

`--scope-classification` is required for combined-chain N/A.
`--chain-observer-receipt` is required for a target-local combined-chain pass.
The unused option may be omitted. Neither record may live beneath the candidate
root.

Before any candidate code runs, the trusted runner computes the complete
tracked `candidate..worktree` patch with `git diff --binary --full-index`,
requires its SHA-256 to equal the patch reviewed by the exact-diff Agent, and
extracts the checker from the immutable candidate Git tree. That checker loads
the lifecycle validator and capture-tool digest directly from content-addressed
candidate Git objects, never from a mutable sibling after a prior hash check.
Validation runs against a host-frozen read-only tree and records the forward
digest before and after. A worktree checker, validator TOCTOU, an unreviewed
post-freeze edit, or a signed receipt without this binding cannot promote.
