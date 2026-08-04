# HARP Combined Lifecycle Chain and Historical Replay

Use this reference when an iteration can change queue, handoff, review,
artifact, completion, retry/resume, or workflow-health behavior. It defines two
additive gates: a target-local combined lifecycle-chain test and a sanitized
historical replay corpus. Neither gate replaces unit tests, regression tests,
the one-hop atomic sandbox, exact-diff adversarial testing, or a real-provider
cell when a provider boundary is reachable.

## Contents

- [Required Chain](#required-chain)
- [Baseline and Incident-Derived Replay Archetypes](#baseline-and-incident-derived-replay-archetypes)
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

When Plan Review can install a graph or admit queue work, treat current-input
resolution as a mandatory pre-chain admission edge. Invoke the real
contract/capture resolver, deterministic graph audit, Plan Review decision,
graph installer, and queue-admission consumers. The reviewer must compare the
proposed immutable-input hashes and declared acceptance scope against the
current contract and every current required capture at review time. Stale,
absent, foreign, or incomplete identities must yield one typed rejection before
installation or launch; a provider-successful review turn cannot make them
current. Bind this pre-chain edge in the same causal trace, observer receipt,
incident fixture, and external-verifier completeness check as the ten stages.

When graph/plan projections are reachable, stage 6 includes the real accepted
graph, queue, DAG, canonical active-plan, route, and next-round admission
consumers. A terminal queue/DAG must converge the lifecycle exactly once under
restart/concurrency; immutable graph-template `pending` intent and stale older
open rows cannot keep selecting executor continuation. When evidence manifests
are reachable, the stage-5-to-stage-7 edge must pass through the real manifest
finalizer. Only an explicit accepted Result Review bound to the exact plan,
attempt, evidence identity, reviewer identity, and nonempty review time may
produce an accepted manifest. Missing, foreign, attempt-mismatched, or
timestamp-empty review facts remain fail-closed inputs to artifact/completion.

At minimum, assert both directions:

- Happy path: handoff identity survives every hop, review is accepted by the
  completion consumer, required artifacts pass, completion becomes true,
  health becomes healthy, and later periodic audits do not emit repeated
  zero-work wakeups.
- Failure path: each replayed inconsistency is detected at its first
  authoritative consumer, routed to an explicit owner or typed pause, cannot
  produce premature completion, and remains eligible for a later health audit.

## Baseline and Incident-Derived Replay Archetypes

Maintain exactly one sanitized baseline profile for each archetype:

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

The baseline three are necessary but not sufficient when the current incident
has another causal shape. Add one sanitized incident-derived profile for every
distinct observed chain and bind it separately in the iteration contract,
external pinned verifier, combined receipt, and host attestation. Do not merge
distinct failures merely because their final health color or provider status is
the same.

Each incident-derived profile must carry a closed causal inventory:

- host-capture and source-snapshot digests;
- typed predecessor and post-state identities;
- concrete producer inputs, outputs, and event kinds, including negative event
  polarity rather than only an umbrella label;
- every downstream consumer that can change graph, queue, review, artifact,
  completion, recovery, or health truth;
- the current contract/capture resolver inputs and exact Plan Review-time
  identity comparison whenever reviewed graph installation is reachable;
- restart/concurrency ordering and an executable oracle for each causal fact;
- the observed failure signature and intended fail-closed terminal or successor route.

For graph/admission incidents, replay accepted-versus-pending convergence,
later distinct-graph reviewability, equal pre/post semantic revisions,
completed-row preservation, and one successor generation. For repair incidents,
replay provider transport separately from the typed machine decision, including
missing/malformed output, unchanged command/input/output identity, bounded
terminal/upstream routing, and one retry only after a canonical causal revision.
When queue launch consumes provider-circuit state, replay selected-provider
resolution through the actual placeholder admission, launch claim, worker
pre-call guard, final backend selection/transport admission, and recovery
consumer. A recognized healthy selected provider must remain launchable while
an unrelated provider is frozen, with the unrelated event/probe bytes unchanged.
Linearize the final exact circuit check and provider side effect under the
selected provider's call lease. If freeze wins, the exception/fact must retain
the exact frozen observation from the decision snapshot and the transport call
count remains zero; if the call wins, the freeze transition waits until that
admitted call releases custody. The selected frozen provider, unknown routing,
and provider identity drift between admission, worker, or final backend must
produce typed no-wrong-provider outcomes; the runtime must not guess, globally
thaw, or silently switch. Distinguish a true pre-call block from a delegated
backend drift after the bound orchestrator already returned: the latter records
partial-call truth while proving the drifted provider was not called. Recovery
requires the exact `(provider, freeze_observation_id)` event, rechecks current
non-frozen state under the same provider lease, and uses a full-row queue CAS.
A stale same-provider recovery event, a missing historical observation identity,
or a concurrent terminal/superseding/new-attempt write must remain fail-closed.
Also replay the decision-to-writer edge under concurrent updates to the same
queue row. Bind the typed decision to a stable semantic attempt and causal
revision. Projection-only churn must rebase and commit that decision exactly
once without recalling the provider; a real semantic-attempt change must reject
or supersede it exactly once. Repeating the same prompt after
`stale_decision_ignored` fails the replay even if each provider turn returns a
valid machine decision. Add a real overlap cell in which one ordinary tick has
persisted repair custody and is waiting on the provider while another ordinary
tick loses the physical repair lock. The lock loser must not publish a competing
subject-row projection; the first typed decision must commit once, restart must
not recall the provider, and no durable supersession may bind equal decision and
current semantic identities. Extend that overlap past provider return and through
the final decision commit or durable semantic supersession. The lock needs a
unique owner token, and release must verify that token so an old owner cannot
unlink a successor's custody. Inject occupied identities for derived retry and
route rows after the provider returns: the existing typed decision must select
another unoccupied identity under the same custody or produce a distinct durable
nonsemantic receipt, without provider recall or false semantic supersession.
Decode the typed JSON with duplicate-key detection
at every object depth. Duplicate action or nested authority keys are malformed
and must fail closed without retry, route, or success transition.
For terminal-projection incidents, replay raw immutable graph intent separately
from queue/DAG lifecycle truth, stale older plan rows, route selection, typed
semantic recovery, and exactly one next-round Planner or actionable terminal
fact. For review-manifest incidents, replay missing, foreign,
attempt-mismatched, and timestamp-empty Result Review facts through the actual
manifest, artifact, completion, and health consumers; none may default to
accepted.
For Plan Review incidents, replay the current contract/capture resolver through
the deterministic graph audit, review decision, installer, and queue consumer.
Include a superseded contract hash, a missing current capture, a foreign capture
identity, and an incomplete source/acceptance boundary; each must reject before
install or Executor launch, while one exact current-input graph remains
reviewable.
Directly injecting `canonical_directive_event`, always returning a valid
`EXECUTOR_REPAIR={...}` object, or starting from a clean workspace omits the
failure mechanism and cannot satisfy the incident gate.

## Read-Only Capture and Sanitization

Capture historical source workspaces only with the bundled whitelist script:

```bash
python3 skills/delivery-alignment-iteration/scripts/capture_harp_history_replay.py \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --source LABEL=ARCHETYPE:/absolute/read-only/workspace \
  --output-dir skills/delivery-alignment-iteration/assets/harp-history-replays
```

The bundled command captures the three baseline profiles. When an incident
requires fields outside that fixed whitelist, use a contract-declared,
host-controlled read-only capture adapter for the smallest additional typed
shape. Bind its immutable tool hash, double snapshot, source digests,
sanitization receipt, and derived profile hash exactly as for the baseline. The
candidate may consume that copied profile but may not choose its own capture
authority or read the historical source during validation.

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
- `historical_replay_gate`: baseline fixture manifest, read-only capture
  command, trusted capture receipt, replay invocation, archetype assertions,
  every contract-bound incident fixture/capture receipt, and durable validation
  evidence.

The combined receipt binds the contract invocation, immutable candidate,
target-local test path and SHA-256, baseline and incident fixture-manifest
SHA-256 values, and a
producer/consumer/assertion triple for all ten stages. It records all three
archetype results and happy-path invariants, and has
a valid host-controlled attestation from outside the candidate repository. If a
legacy HMAC receipt is still consumed, only the external verifier/signing host
may read the symmetric secret; candidate processes inherit neither the secret
nor its path. The
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
external pinned validator and verifier must fail closed for a missing stage,
changed fixture hash, leaked absolute path, missing source provenance, absent
baseline or contract-bound incident, dropped causal fact/edge, incomplete
closure assertion, or nonzero repeated zero-work wakeups.

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

The external phase ledger binds these receipts. Validate finite closure with a
pinned verifier outside the HARP candidate repository:

```bash
python3 /trusted/skills/delivery-alignment-iteration/scripts/check_iteration_convergence.py \
  --contract docs/iteration_contracts/<iteration>.yaml \
  --ledger /external/phase-ledgers/<iteration>.json \
  --candidate-root . \
  --public-key /external/trust/ledger-ed25519-public.pem \
  --expected-verifier-sha256 <host-pinned-sha256> \
  --require-close --json
```

The ledger gate rows point to the separately signed scope-classification record
for combined-chain N/A and the call-boundary observer receipt for a required
target-local pass. Neither the ledger nor either host record may live beneath
the candidate root.

Before any candidate code runs, the trusted runner computes the complete
tracked `candidate..worktree` patch with `git diff --binary --full-index`,
requires its SHA-256 to equal the T2.5-reviewed patch, then loads the verifier
and lifecycle validator from the installed, version-pinned external TCB. The
verifier treats candidate checkers, traces, and manifests only as evidence and
semantically parses every receipt it authorizes. Validation runs against a
host-frozen read-only tree and records the forward digest before and after. A
candidate-origin checker, candidate-visible private key, path-only hash check,
validator TOCTOU, opaque receipt, unreviewed post-freeze edit, or receipt without
this binding cannot promote.
