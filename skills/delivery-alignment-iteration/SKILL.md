---
name: delivery-alignment-iteration
description: Use when planning, implementing, reviewing, or handing off a project iteration where the user cares about exact alignment between requested intent, acceptance criteria, implemented diff, tests, handoff state, and final claims; especially for HARP iterations, prior delivery mismatches, "货不对板", runtime repair work, docs, skills, prompt changes, repository hygiene or refactors, vendored/generated artifacts, evidence retention, technical-debt ratchets, release updates, or branch/workspace synchronization.
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
   Run the Canonical Control-State Audit below whenever a changed behavior can
   alter an effective control outcome, even if the implementation labels the
   change as projection, context, repair, migration, or quality plumbing rather
   than a state transition.
   Run the Repository Stewardship Gate below whenever the iteration can
   materially change repository footprint, generated or vendored artifacts,
   evidence retention, architectural concentration, static-analysis debt,
   packaging, release contents, or Git history.
4. Write deliverables and non-goals. If a requested deliverable is impossible or unsafe, state that before substituting anything.
5. Implement in small bounded changes. Do not silently replace the requested artifact with an adjacent artifact.
6. Update the handoff after every material implementation, verification, blocker,
   scope, or decision change. Do not postpone it until the final response.
7. Maintain a traceability matrix: each acceptance criterion must map to changed files and verification evidence.
8. Classify the candidate diff and apply the diff-directed adversarial gate
   below. For a high-risk diff, a real adversarial Agent must generate attacks
   from the actual diff; a static checklist, hand-written test list, or prompt
   inspection does not satisfy the gate.
9. Run at least one atomic sandbox in every iteration—not only broad regression
   or a full benchmark run. When the changed system has an Agent, provider,
   prompt, role, or handoff boundary, invoke a real provider against the
   smallest real slice and record prompt, raw output, parsed result, downstream
   fact, and deterministic assertions. A provider-free deterministic system may
   instead exercise its real changed boundary without adding an AI dependency;
   record a deterministic unreachability proof for the provider path.
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

Use strict YAML for every schema-version-2 machine contract. Historical
version-1 Markdown remains read-only; do not extend its permissive parser.
Keep human narrative in the separate Markdown handoff. Include these fields:

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

## Diff-Directed Adversarial / Flow-Diffusion Gate

Use `adversarial` to mean counterexample-seeking, not an assumption that a
malicious actor exists. Start from expected operators, providers, artifacts,
and happy-flow transitions, then diffuse into plausible neighboring or
interacting flows that can expose focal bugs. Permit combined dimensions when
their interaction is the suspected failure mechanism; do not impose a
one-perturbation rule. Keep the schema terms `attacks` and `escaped attacks` for
backward compatibility, but interpret them as executable counterexamples and
unresolved counterexamples.

Preserve generalization concerns even when they do not establish a current
failure. Record them separately from `attacks`, with the missing execution-path
evidence or future trigger that would make them testable. They inform later
diffusion scopes but do not fail the current deterministic gate.

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
   deterministic oracles. Diffuse happy flows across nonzero exits, missing
   returns, crash windows, stale identities, concurrent writers,
   malformed-but-schema-valid payloads, partial publication, projection
   disagreement, and interacting dimensions when relevant.
3. Isolate the Agent from the intended fix and expected answer. Permit it to
   write only tests, repros, manifests, and evidence—not product source.
4. For a bug fix, prove the frozen negative on the base and prevention on the
   candidate when safe. For a new module, use boundary-valid mutations,
   neighboring-flow substitutions, fault sequences, or other minimal
   counterexamples to prove that the generated test can fail for the defect it
   claims to detect.
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

## Repository Stewardship Gate

Use this gate when a locally correct delivery can worsen the repository's
long-term authority, reproducibility, maintainability, release purity, or cost.
Turn applicable rules into acceptance criteria and before/after evidence; do not
leave them as optional cleanup advice.

### Measure separate budgets

Measure tracked source, generated/ignored checkout, dependencies, durable
artifacts, duplicate content, and Git object/history growth separately. Set
explicit ceilings or non-regression baselines for the dimensions the diff can
change. Do not use total checkout size as a proxy for source size, and do not
hide growth by moving it between categories.

### Preserve one authority per artifact

Choose one authoritative form for source, vendored inputs, generated outputs,
and release bundles. Treat every other form as reproducibly derived: pin its
producer and version or commit, record hashes, and provide one verified
regenerate, fetch, or publish path. Do not hand-maintain source and build output
as peer truths. Keep dependency caches and local install trees ignored unless
the contract explicitly requires an immutable checked-in artifact.

### Tier evidence by purpose

Keep the public reproducibility bundle bounded and independently usable:
include the minimum inputs, manifests, commands, environment/lock data, hashes,
accepted outputs, and claim-to-evidence links needed to reproduce or audit the
public result. Route full workspaces, raw traces, databases, checkpoints, and
bulky forensic evidence to a declared internal archive, release artifact, LFS,
or object store with retention and access policy. Never delete or relocate the
only authoritative evidence merely to satisfy a size target.

### Reduce architectural concentration

Before extending a large or high-churn module, inventory its responsibilities
and identify pure state transitions, policy decisions, and I/O adapters.
Prefer deletion, convergence, or extraction behind characterized interfaces to
another branch, compatibility lane, fallback, or god-object method. Preserve
behavior with boundary tests; file count or line-count reduction alone is not
proof of a better design.

### Ratchet quality debt

Record full-repository lint, type, test, coverage when relevant, package
contents, size, and duplicate baselines. The candidate must not worsen them
without a reviewed exception, owner, expiry condition, and removal action.
Tighten checks at touched boundaries and shrink suppressions incrementally; do
not require an unrelated whole-repository rewrite, and do not use legacy debt
to excuse new debt.

### Prove releases in a clean room

Build public release artifacts from a fresh clone or equivalent exported tree.
Retain a receipt covering tree cleanliness, wheel/sdist or package contents,
import/install/smoke behavior, size ceilings, forbidden generated paths,
duplicate budget, dependency provenance, and reproduction instructions. A
successful build from a dirty developer checkout is supplementary evidence,
not release proof.

### Protect irreversible history and storage operations

Treat published Git history, evidence deletion, authoritative-store migration,
force pushes, and public URL changes as destructive by default. Prefer forward
fixes, external artifacts, LFS, or a clean public mirror. Require explicit
human authorization, exact targets, verified backup, consumer/citation impact,
cutover plan, and tested rollback before rewriting or deleting. Never infer
permission for an irreversible operation from a general request to simplify a
repository.

## Canonical Control-State Audit

Use this audit whenever a diff or design touches a control state, identity,
transition, reducer, writer, reader, projection, retry, resume, owner, wakeup,
admission, completion, or migration.

Use the project's declared canonical control mechanism. In HARP this is the
typed-event supervisor transaction and canonical reducer. A provider-free or
non-event-sourced repository may use an atomic database transaction or another
single authoritative state machine when it proves the same identity,
predecessor, authority, uniqueness, transactional re-read or replay, and
reader-equivalence invariants applicable to its declared mechanism. Do not
redesign a repository into HARP merely to satisfy this audit.

For HARP and equivalent event-supervised architectures:

- a control outcome is any effective state, owner, wakeup, retry, admission,
  graph, queue, completion, or human-pause decision;
- a canonical event is accepted only through the canonical transaction, which
  verifies producer identity and authority, binds subject/revision/payload hash,
  and assigns monotonic `event_seq` independently of filenames, timestamps, or
  prose ordering;
- canonical identity is an injective typed tuple. Alias equivalence requires its
  own authorized canonical event; normalization may not collapse distinct
  workspace, contract, lineage, namespace, or entity identities;
- the reducer revision includes immutable schema, transition-table,
  implementation, owner-policy, and identity-normalization digests;
- an Agent's scientific or qualitative verdict is free content. The deterministic
  control fact is that an authorized, provenance-bound verdict event was
  recorded—not that the reducer agrees with or reproduces the judgment. Event
  kinds and control-significant fields are closed and reducer-defined: an
  authorized Agent may choose an allowed verdict value, but free prose or an
  opaque payload may not invent a transition kind or its control meaning.

A state transition is admissible only when one canonical transition revision
or atomic transaction contract contains sufficient typed evidence for all of
the following:

1. the project-declared injective typed subject identity. For HARP this includes
   workspace, contract revision, entity, parent lineage, predecessor identity,
   and relevant payload hash; other mechanisms must enumerate their own
   sufficient tuple rather than synthesize inapplicable HARP fields;
2. the exact predecessor state and state revision;
3. typed causative commands or events allowed by that predecessor state,
   applied in the mechanism's canonical transaction order—monotonic event
   sequence for HARP—to one unique result;
4. deterministic transition preconditions evaluated against that same revision;
5. the current owner or admission identity and its authority;
6. exactly one post-state revision plus its applicable durable wakeup or
   terminal fact.

The same command/event packet, canonical predecessor/admission snapshot, and
transition revision must produce the same result in every deployed process and
service that can affect a control outcome.

Timestamp order, file order, a later plan or review, model prose, a template
recommendation, an inferred process state, a missing file, or a Web/report
projection is not sufficient authority. A consumer that cannot prove a
transition from canonical facts must emit a typed
`reconciliation_required` observation for the configured reconciliation owner;
it must not guess or call a provider to reconcile deterministic state. If that
owner cannot be proven live and authorized from canonical facts, the reducer
must preserve the unresolved entity and enter a typed human pause with a durable
wakeup; missing ownership may not strand or terminate the entity. Apply these
reconciliation event names and wakeup semantics when the project declares such
an asynchronous owner path; a synchronous atomic system must instead fail the
transaction without changing canonical state.

`reconciliation_required` does not assert or perform the disputed transition.
It appends a node-attached observation while leaving the subject state
unchanged, and is admissible from the proven subject identity/revision, typed
failure class, reducer-bound owner policy, and durable wakeup. This recovery
event therefore does not require evidence that only reconciliation can produce.
Its semantic identity is deterministic over subject revision and failure class,
so duplicates coalesce. Claim uses a renewable ownership lease; lease loss or
owner death deterministically reopens the wakeup, and repeated failure enters
typed human pause rather than creating an unbounded observation frontier.

For each changed control entity, the iteration evidence must enumerate:

- every state and allowed next command or event;
- exact project-declared identity and predecessor bindings;
- the single reducer writer and every mutation entry point, each mechanically
  forced through that reducer;
- every reader and projection;
- owner, wakeup, retry/resume, terminal, and replay semantics;
- each legacy or heuristic authority path removed by the candidate.

Do not treat a writer allowlist as proof of a single semantic SSOT. Two
recognized projections interpreted differently by two consumers are still
split-brain. JSON, Markdown, prompt context, templates, Web views, reports, and
compatibility files must be revision-bound read-only projections; they may not
close, supersede, select, or synthesize control truth.
Canonical identity normalization must prove when aliases denote the same
subject. For the same normalized subject and revision, every deployed
reader/projection that can affect a control outcome must pass a deterministic
semantic-equivalence oracle for effective state and allowed next events;
syntactic revision binding alone is insufficient. A nonconforming reader must
be removed from the control path, not relabeled unsupported.
Each reader is compared directly with the canonical transition oracle, not only
pairwise with other readers. Inventory completeness must cover transitive adapters, caches,
prompts, environment inputs, triggers, plugins, CLIs, RPCs, and direct-store
access; tainting any noncanonical input while canonical facts are fixed must not
change a control outcome.

Apply Occam's razor at the state-machine boundary:

- define the legal typed states and transitions once; do not maintain a parallel
  forbidden-state blacklist;
- prefer deleting consumer-local inference and duplicate mutable projections to
  adding conflict-specific branches;
- keep shadow replay read-only and bounded; do not create a long-lived
  dual-writer or dual-reader compatibility lane. Its sunset revision and removal
  condition bind a stable migration-lane identity. Extend it only when
  deterministic replay proves the scheduled cutover would violate canonical
  conservation, and only with explicit human authorization, an exact defect,
  one bounded replacement sunset, verified backup, and rollback evidence.
  Convenience or incomplete work is not an extension reason. Identity includes source/destination schema,
  stores, predecessor lane, and effective readers/writers, so rename or adapter
  replacement cannot reincarnate it. At cutover, no legacy/shadow read or write
  may remain on a control path;
- use deterministic admission for identity, set conservation, predecessor, and
  lifecycle facts. Scientific or qualitative judgments remain Agent freedom:
  runtime may record their exact typed verdict and provenance, but may not
  replace the judgment with deterministic quality heuristics;
- if an unavoidable conflict cannot be reduced deterministically, assign it to
  the configured reconciliation owner with a durable wakeup; if that ownership
  cannot be proven, enter the typed human pause defined above.

Any candidate that can alter an effective control outcome is high risk under
the Diff-Directed Adversarial Gate; self-classification cannot downgrade it.
Deterministic completion additionally
requires:

1. a bounded model explorer over the changed state/event product, with the
   transition table or reducer as oracle;
2. crash injection immediately before and after every durable boundary reachable
   from the changed state/input product, including textually unchanged writes
   whose interpretation, transaction, ordering, or ownership semantics changed,
   followed by replay or transactional re-read proving one unique result for
   every state revision and for each owner, frontier, or wakeup field that the
   declared mechanism makes reachable;
3. stale identity, duplicate event, concurrent writer, partial publication,
   projection disagreement, timeout, and owner-missing sequences where
   reachable in the bounded transition model. Any excluded class needs a
   deterministic unreachability proof from that model;
4. when an Agent/provider consumer is reachable from the changed state product,
   a real-provider atomic sandbox proving Agents can consume the canonical
   packet without inventing authority. Holding canonical facts constant,
   provider output or availability must never change transition truth; the
   sandbox validates consumption only. For a provider-free state product,
   record deterministic unreachability and exercise the real non-provider
   boundary instead;
5. the exact-diff adversarial gate. The adversarial Agent expands attack
   sequences; it does not define transition truth and may emit events only into
   the isolated test fixture, never the candidate or production event stream.

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
  replaces the real changed boundary. Agent/provider changes require a
  successful real-provider cell; provider-free changes require a real
  deterministic boundary run plus proof that no provider path is reachable.
- Do not substitute a full AIRS/benchmark run for a missing atomic sandbox when the change is localized to one boundary.
- Add or extend a sandbox when subtracting over-engineered machinery, not only when adding new machinery.

## When To Read References

Read `references/iteration_contract_schema.md` when creating a durable contract, reviewing a mismatch, or adapting the schema for a repository.
