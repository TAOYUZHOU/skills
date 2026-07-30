## Iteration objective

Publish a clean-room, reproducible runtime release while reducing repository and architectural risk. Repository cleanup, evidence deletion, and history rewriting are separate workstreams; none is considered necessary for the runtime release itself.

## Execution plan

1. Baseline and classify

   - Record immutable base commit and target release branch.
   - Measure separately:
     - tracked authored source;
     - tracked/ignored generated output;
     - dependency environment;
     - raw traces/checkpoints;
     - report/evidence bundles;
     - duplicate content;
     - Git object/history size.
   - Capture full-repository Ruff, Mypy, tests, coverage, package contents, and installation/smoke baselines.
   - Identify authoritative source, generated artifacts, release inputs, and evidence stores.

2. Establish release and retention boundaries

   - Make authored source plus pinned manifests/lockfiles authoritative.
   - Treat frontend/build output as reproducibly generated; exclude it from source control and release unless runtime-required.
   - Keep the 9 GB local environment ignored and replace it with pinned dependency metadata.
   - Deduplicate generated assets and retain one authoritative input or generation path.
   - Define:
     - a bounded public reproducibility bundle;
     - an access-controlled internal evidence archive;
     - retention dates, owners, and deletion candidates.

3. Decompose the 4,000-line runtime module

   Extract behind characterized interfaces, in this order:

   - pure state transitions and canonical state model;
   - scheduling/admission policy;
   - subprocess I/O adapter;
   - Web read-only projection.

   Inventory every state mutation entry point, reader, projection, retry/resume path, owner, wakeup, and completion rule. Force mutations through one canonical transaction/state-machine path. Web output must remain revision-bound projection, never control authority.

4. Apply quality ratchets

   - Require zero new Ruff or Mypy violations in touched code.
   - Tighten typing and linting at extracted interfaces.
   - Do not require unrelated repository-wide debt to reach zero.
   - Require full-repository debt counts to be no worse than baseline.
   - Any exception needs an owner, rationale, expiry condition, and removal action.

5. Verify the high-risk candidate

   Because executable state, scheduling, I/O, projection, and release behavior change, classify the diff as high risk.

   Required evidence:

   - characterization and boundary tests;
   - bounded state/event model exploration;
   - crash injection around durable boundaries;
   - stale identity, duplicate input, concurrent writer, timeout, partial publication, owner-loss, retry, and projection-disagreement cases;
   - direct equivalence checks between every effective reader and the canonical state oracle;
   - exact-diff adversarial tests generated from pinned base and candidate commits, with zero escaped executable counterexamples;
   - one atomic sandbox exercising the real changed boundary;
   - fixed regression suite.

6. Prove the release in a clean room

   From a fresh clone or exported clean tree:

   - install from pinned dependencies;
   - regenerate required frontend/assets;
   - build wheel/sdist or declared distribution;
   - inspect package contents and forbidden paths;
   - run import, startup, subprocess, state-transition, and Web-projection smoke tests;
   - reproduce the accepted output and verify hashes;
   - record commands, tool versions, commit, artifact hashes, sizes, and results.

## Authorization boundary

May proceed without additional authorization:

- read-only inventory and measurements;
- defining retention and release policies;
- refactoring on an unpublished working branch;
- tests, static analysis, clean-room builds, and local sandboxes;
- creating archives by copying evidence while preserving originals;
- removing reproducibly generated files from a candidate checkout or release artifact, without deleting their authoritative source;
- preparing a history-rewrite plan, dry-run mapping, and replacement repository/mirror.

Requires explicit human authorization before execution:

- deleting any raw traces, checkpoints, reports, or other potentially authoritative evidence;
- moving the sole evidence copy to another store;
- rewriting published history or force-pushing;
- changing public URLs or release references;
- deleting remote branches/tags or invalidating existing commit citations.

Authorization must name exact targets and include a verified backup, affected consumers/citations, cutover window, communication plan, and tested rollback. Prefer a smaller clean public mirror or forward cleanup over rewriting shared history.

## Evidence placement

Public bundle:

- source revision and release artifacts;
- dependency locks and producer/tool versions;
- minimal reproducibility inputs;
- regeneration/build/test commands;
- accepted outputs and hashes;
- claim-to-evidence index;
- license/provenance information.

Internal only:

- complete raw traces and prompts;
- checkpoints and intermediate databases;
- failed or sensitive experiment outputs;
- adversarial raw outputs and forensic logs;
- credentials, machine paths, private data, and security-sensitive crash details;
- backup and rollback material for any history rewrite.

Public evidence must be independently usable; internal evidence must have an owner, access policy, retention deadline, and integrity manifest.

## Improvement measures

Set exact ceilings after the baseline, then require:

- release artifact contains no local environment, raw workspace, cache, or unintended build tree;
- generated assets have one authority and one verified regeneration path;
- duplicate bytes and generated checkout footprint decrease materially, with no category merely moved elsewhere;
- the 4,000-line module loses at least the four mixed responsibilities; boundary coverage and mutation-path count matter more than line count;
- touched-code Ruff and Mypy debt is zero;
- repository-wide Ruff/Mypy/test/coverage results do not regress;
- all clean-room commands succeed from documented inputs;
- package and public evidence sizes remain within recorded ceilings;
- zero escaped adversarial counterexamples.

## Release blockers

Block release for any of the following:

- dirty-checkout-only build evidence;
- unpinned dependencies or generators;
- unreproducible required frontend/assets;
- multiple mutable authorities for state or generated artifacts;
- Web projection or subprocess observations influencing control state outside the canonical transition path;
- failing tests, touched-code lint/type violations, or worsened repository-wide debt without an approved exception;
- incomplete package-content/provenance inspection;
- missing artifact hashes or reproduction instructions;
- unresolved executable adversarial counterexample;
- missing rollback-capable archive for evidence/history operations;
- release depending on an unauthorized deletion or force-push.

The runtime release may proceed before storage deletion or history rewriting. Those destructive operations should remain separately approved post-release changes.