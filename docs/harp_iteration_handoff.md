# HARP Iteration Handoff

status: partial
updated_at_utc: 2026-08-02T22:38:37Z
iteration: delivery-alignment-incident-derived-replay
contract: docs/iteration_contracts/delivery_alignment_incident_derived_replay_20260802.yaml
candidate: 09f50941957c849bc12445d233d8f9fd8223c10e

## Current incident-derived replay addendum

### Intent

Make the existing three sanitized replay archetypes a baseline rather than an
exhaustive catalog, and require every distinct available incident signature to
be replayed through its real causal producer-consumer chain.

### Non-goals

- Do not modify HARP runtime code or any live workspace state from this skill iteration.
- Do not claim that skill policy repairs Biopharma, Synthetic, or Target C.
- Do not replace existing atomics, regression, provider boundary, exact-diff, review, deployment, or observation gates.

### Current truth

- The prior skill iteration is frozen at `09f50941957c849bc12445d233d8f9fd8223c10e` and correctly enforces a ten-stage chain plus exactly three baseline historical profiles.
- The new Biopharma host capture proves a different chain: accepted graph restaged as pending, concrete negative graph/repair events misclassified as positive semantic evidence, a completed equal-pre/post admission, then permanent duplicate denial.
- The new Synthetic host capture proves another chain: three successful provider transports with no typed `EXECUTOR_REPAIR` record were defaulted to retry despite prose `terminal_fail`, rerunning unchanged scientific work until budget exhaustion.
- The later Synthetic progression adds the required positive/negative distinction: a repair Agent made a real source/test revision and requested retry in prose, but still omitted the machine record; runtime launched an equal-command successor by default without hash-binding that causal revision. Equal command text alone therefore cannot classify a retry, while prose or a repair artifact still cannot authorize one.
- The new Target C host capture proves a third chain: queue and DAG are terminal while immutable graph intent remains pending and two older canonical plan rows keep selecting executor continuation; the same terminal path writes three evidence manifests as accepted without a timestamped bound Result Review.
- The Target C Plan Review addendum proves an earlier fail-open edge: deterministic review approved and installed tc10 with a superseded contract hash, no binding to the current Target C capture, and incomplete causal source authority. Provider/reviewer success did not make those inputs current.
- The Target C repair-CAS addendum proves that typed output alone is insufficient under concurrency: two valid `terminal_fail` decisions lost per-item CAS solely because `output_assessment_reconciled_at` advanced, and triggered a third equal-prompt provider call while the semantic blocked attempt remained unchanged.
- The first immutable bootstrap exact-diff was rejected before deployment: while one tick waited on the provider under persisted repair custody, a lock-losing ordinary tick wrote the same subject row, produced an equal-identity supersession receipt, and permanently suppressed the already-produced decision. The same candidate accepted duplicate JSON `action` keys with last-wins retry semantics.
- The second immutable bootstrap exact-diff was also rejected before deployment: physical custody ended after provider return but before decision commit, so another tick called the provider for the same identity; a derived retry-row collision also discarded the existing decision and later recalled the provider.
- The latest Target C live capture adds a provider-scope transmission gap: the queue placeholder blocked tc10b because unrelated `openai_compat` was frozen, although the selected `codex_app_server` provider succeeded later. Exact call guards were already correct; the omitted queue/worker edge caused the P0.
- Exact candidate-chain audit then exposed four adjacent provider edges that provider-name atomics did not cover: final backend re-resolution after the worker guard, false no-call projection after an orchestrator call followed by delegated drift, loss of the exact freeze observation across a decision/re-read race, and stale recovery overwriting a concurrently changed queue row. The required replay now binds final transport admission under the provider call lease, partial-call truth, exact freeze identity, and recovery CAS.
- The current focused executor-repair and historical replay selectors pass 29/29 while the exact three-output parser reproduction still returns `default_retry_after_successful_repair_agent`; baseline coverage is therefore insufficient.

### Current phase

The schema-v2 addendum contract is frozen and the bounded D1/D2 policy change is
implemented in the dirty worktree. Its first real bootstrap consumer is now
immutable at `bc3e8cb0353cda32e89b7cb53d30d3afe7446d0b` from stable base
`39b59a59db6d05e6c7ed1b81c0a610cac1ccb752`, with canonical full-index diff
`5bcce9010c5f38b49779e3466a1f4eec9272d0f1986fceb1ac330cc068ed1f6b`;
independent exact-diff review and deployment remain open. The first policy draft
was rolled back before contract freeze. No live workspace, provider, process,
cron, or review state has been changed by this addendum.

### Completed changes

- Read the full skill-creator workflow and re-audited the delivery-alignment skill and combined-chain reference.
- Bound all three read-only Target C host captures and the executable 29/29 coverage-gap reproduction into the addendum contract.
- Bound the later Synthetic causal-revision progression so future fixtures must distinguish blind equal-command retry from one retry authorized by a valid machine decision over a canonical source revision.
- Made the three bundled profiles an explicit baseline and required every distinct available incident signature as additive replay evidence.
- Added causal-fact/producer-consumer completeness, concrete negative event polarity, provider-transport-versus-machine-decision separation, graph/admission concurrency, and unchanged-retry suppression rules.
- Added terminal graph/DAG/canonical-active-plan convergence, one next-round owner under restart/concurrency, and fail-closed missing/foreign/attempt-mismatched/timestamp-empty Result Review manifest rules.
- Added a mandatory current-contract/current-capture resolver edge at Plan Review and stale/missing/foreign/incomplete negative cells that must reject before graph installation, queue admission, or Executor launch.
- Added semantic-attempt-bound decision commit/rebase: projection-only row churn must not recall the provider, while real semantic identity change must supersede or route once.
- Added the rejected exact-diff overlap/parser counterexamples: physical-lock losers cannot write a competing subject projection, equal decision/current supersession is invalid, and duplicate keys at any JSON object depth fail closed.
- Extended custody replay through post-provider commit with an owner token and owner-checked release, and required retry/route row collision recovery to reuse the existing decision without provider recall.
- Added selected-provider queue/worker transmission replay with unrelated-frozen pass-through and selected-frozen, unknown-routing, and identity-drift no-call cells.
- Extended selected-provider replay through final backend/call-lease admission and exact freeze-observation recovery; added accurate delegated partial-call truth plus stale-event and concurrent-recovery-CAS cells.
- Preserved the prior completed iteration and unrelated dirty repository state.

### Verification evidence

- Preimplementation skill HEAD: `09f50941957c849bc12445d233d8f9fd8223c10e`.
- Biopharma capture SHA-256: `58afd4bb40aeb82d38e32644828a5bb24f5178dbd93dd7e75372fb0b7fe2a129`.
- Synthetic capture SHA-256: `d35a7df6afc0f5b4b527eca438e015d15e3268398f42766130097f761d105d7c`.
- Synthetic recovery-progression SHA-256: `366b0d1355f94f8e04cf3869e29ad18ede32f30a8bc3f38eece3de89831f1a6f`.
- Target C terminal-projection/review-manifest capture SHA-256: `1cfb6097da09beb42c13fc89579352462ae00d439e02b607da3c5606f1102e97`.
- Target C stale-contract Plan Review addendum SHA-256: `a452ffe7c5c5aae03bb21d28f75a205a6a611d0f8313bbfafaaef37f9b282ed6`.
- Target C repair-CAS addendum SHA-256: `fa6b50983041621b6120ad623f45f8cda6186c84eecca2159988a6da561d3565`.
- Target C bootstrap exact-diff rejection addendum SHA-256: `c2eed24abcc4820500670ff64a7a3bddba4a9a2ec8238863ac738e619bf1beec`.
- Target C bootstrap exact-diff rejection v2 addendum SHA-256: `d569d536cd7ea746f8dbd43e17e1d42a421a988fb604a0ae9a49ad4b26633184`.
- Target C selected-provider queue-freeze addendum SHA-256: `5cb2d8bb5792a9f2dcef996341d9daa12f23dc23ce2f468fdcf6cd49c4510951`.
- Coverage-gap reproduction SHA-256: `b9366bf0b716219ecd6d02e3185afef0dbfb34ca8d1a5b88fde73bf5c8ac5e1c`.
- `quick_validate.py skills/delivery-alignment-iteration`: `Skill is valid!`.
- Targeted deterministic suite: **116 passed**.
- Bootstrap consumer combined runtime suite: **305 passed** on the clean immutable candidate before independent exact-diff review.
- `git diff --check` over the declared addendum paths: passed.
- Current hashes: skill `7a3636b81f9dea85ccefcdf57ce0feb4f4003001aed492228bf20a4c15eb5da4`; reference `8a8bc23c74e1bc13b2eacefce405b313b9eb84b548a59157bf6bb108c963f54d`; contract `e9dcec80be414d2d90414378dd4a3d0480b06f982e24ce903d1ddd01c57c0188`.

### Open blockers and risks

- Immutable skill candidate, skill exact-diff Agent review, bootstrap consumer exact-diff/Change Reviews, and full Target C r4 candidate-origin enforcement remain open.
- The skill repository contains unrelated dirty evidence; only declared addendum paths may be changed.
- No external subagent forward test is run because this session does not authorize subagent delegation.

### Exact next action

Freeze and review an immutable skill candidate together with bootstrap consumer
`bc3e8cb...d0b`; do not deploy the consumer or mark the policy complete until
both exact diffs and independent Change Review pass.

### Final claims allowed now

- The addendum contract is frozen and its bounded policy text passes deterministic validation.
- The prior three-profile skill candidate remains valid for its original scope.
- Incident-derived replay, runtime repair, deployment, and workspace health are not yet complete.

---

## Prior completed combined-chain iteration archive

## Intent

Require applicable high-risk iterations to verify the complete executor-to-health
lifecycle with one combined atomic chain and replace clean hand-authored HARP
workspace mocks with sanitized replays derived from three real workspace histories.

## Non-goals

- Do not repair or mutate the three live workspaces.
- Do not retain raw databases, prompts, scientific artifacts, credentials, or absolute paths.
- Do not replace focused unit, regression, one-hop atomic, clean-room, or exact-diff gates.
- Do not treat historical replay evidence as current live-state or completion authority.

## Current truth

- Canonical skill: `skills/delivery-alignment-iteration/SKILL.md`.
- Current immutable base: `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- Rejected first candidate: `84f7ddeb2c7c1e8c14c9bbf48325f93754627485`.
- Rejected second candidate: `ad783b17d84b55e31fc3655f16586521807de83c`.
- Rejected third candidate: `826c814ab0ece6cacac778089a219798220165ac`.
- Internally rejected fourth candidate: `27316c4b011d0663aeaeb9a046ed16536dac2e1c`.
- Rejected fifth candidate: `6ecd8409ac1c0dc4cdf52673fa45a3c7eeae12b4`.
- Rejected sixth candidate: `876153fc3dc8af5e6c2fa4723f4c9331ab1fb4af`.
- Rejected seventh candidate: `e606effd18de22e5da890fdea6bbbed1295e6c0b`;
- Rejected eighth candidate: `1269274d743d8ba47ee6b35bbdc6045500986d3b`;
- Rejected ninth candidate: `fb93b105d41cf81246065a312b4fd23e75a7df55`.
- Rejected tenth candidate: `ca0359e4d4128f97950c8be63825dbeadd742969`;
- Rejected eleventh candidate: `258047c1d4f5f0cbb4f8c7df0c7b15b4a22f7282`;
- Rejected twelfth candidate: `7d13ec84e5f2cdb581d4131b420e9a9f7fcb64ed`;
- Rejected thirteenth candidate: `333966b13340b9ada510ff068d2db1aa0205f16d`.
- Rejected fourteenth candidate: `dff8bfb36017f2a5784411114083f699b57d7c91`.
- Rejected fifteenth candidate: `e29ae7d6d1f2f15c82c6320d79ac0eff2fdfab1f`.
- Frozen sixteenth candidate: `09f50941957c849bc12445d233d8f9fd8223c10e`.
- Three read-only source histories exhibit distinct classes: accepted-review projection mismatch, blocked missing-artifact dependency, and partial-result materialization.
- The working tree already contains unrelated untracked evidence and skills; they are outside this iteration.

## Current phase

The first frozen candidate failed independent forward and exact-diff review.
The third candidate's exact-diff review found one remaining command/test
semantic split. It was repaired and covered in fourth candidate `27316c4`.
Before sending the fourth candidate to the external Agent, internal review found that
argv membership alone could still be deselected. Constrained pytest plus parsed,
hash-bound JUnit evidence was implemented in fifth candidate `6ecd840`. Its
Agent review then correctly rejected using a metadata test as if it were a real
HARP runtime chain and identified the missing external-candidate CLI binding.
The sixth candidate's forward-bound review found replayable unreachability
attestation and a nested queue-count free-text channel; both are repaired.
The seventh candidate's exact-diff review found that a signed absence observation
could still be replayed into a different repository instance and that the handoff
candidate was not machine-bound. Both now fail closed through a current-root
declarative predicate and a contract/external/handoff three-way candidate check.
The eighth candidate's exact-diff review found an `output_assessment` nested
free-text escape, an author-selectable absence path that did not inventory the
repository, and a signed manifest without an independently bound capture
witness. The validator now closes the nested schema, the checker owns a fixed
repository-wide runtime-boundary inventory, and each real-history capture has a
separately host-attested receipt binding its tool and source/profile digests.
The ninth candidate's exact-diff review found that lifecycle signals could be
split across four modules and that a `missing` assessment could still claim
zero missing artifacts. Repository inventory now unions signals per package and
fails closed on code outside the skill-catalog layout; the blocked-artifact
oracle now requires positive missing count and `checked < expected`.
The tenth candidate's exact-diff review found that a required gate still
accepted meta-validation, that combined N/A could fall back to an arbitrary
absent path, and that lifecycle modules could split across evidence directories
or skill packages. Required receipts now demand the target-local boundary mode,
combined N/A accepts only the fixed inventory, and immutable-diff signals are
unioned repository-wide.
The eleventh candidate's exact-diff review showed that ten vacuous green tests
could still impersonate the chain and that immutable changed paths were scanned
from mutable worktree bytes. Target-local receipts now bind candidate-tree
producer/consumer file hashes plus per-test coverage contexts, while
applicability reads changed code directly from candidate Git blobs.
The twelfth candidate's exact-diff review showed that unrelated autouse calls
could satisfy file coverage, unchanged runtime files could be deleted only from
the worktree, and deleted lifecycle code was absent from candidate blobs. The
required chain now carries a same-run ordered causal digest trace; applicability
scans the complete candidate tree and base blobs for deletions.
The thirteenth candidate's exact-diff review showed that a candidate could emit
an internally consistent causal digest trace without passing real values and
that neutral identifiers could evade a lexical applicability inventory. A
required target-local chain now needs an independently signed, outside-tree
call-boundary observation of actual producer/consumer values. Combined-chain
N/A now needs an independently signed outside-tree classification bound to the
exact repository identity, immutable diff, and complete changed-path set; the
lexical inventory can only contradict that classification.
The fourteenth candidate's exact-diff review showed that the reviewed
post-freeze patch hash was not enforced against the tracked worktree bytes that
the checker executed. High-risk promotion now freezes the complete tracked
forward patch before execution, runs checker/validator blobs extracted from the
immutable candidate, and binds those tool hashes plus the same forward digest
through checker output, provider receipt, and deterministic gate result.
The fifteenth candidate's exact-diff review found a validator TOCTOU between
origin hashing and import. The checker now reads and compiles validator bytes
directly from the content-addressed candidate Git object, injects the capture
tool digest from the same candidate tree, and records the actually loaded hash.
The trusted runner also attests a frozen read-only tree and matching forward
digests before and after validation.

## Completed changes

- Read the complete `skill-creator` and `delivery-alignment-iteration` skills plus the applicable interface/schema references.
- Audited the three live histories without writing their queue, SQLite, cron, or workspace files.
- Defined bounded deliverables and explicit privacy/non-authority constraints for real-history replay.
- Added mandatory Combined Lifecycle Chain and Historical Replay gates to the skill, schema reference, and Agent-facing metadata.
- Added a read-only, double-read-stable, SQLite-query-only capture script and a fail-closed replay/receipt validator.
- Captured three pseudonymous control-shape profiles with no raw database, prompts, free-form output, scientific artifacts, credentials, or absolute source paths.
- Added checker enforcement for required versus deterministically unreachable gates and recomputed evidence validation.
- Added regression tests for missing declarations, evidence tampering, all three historical signatures, ordered chain stages, and manifest binding.
- Added a trusted capture receipt and a fixed current-root runtime-boundary
  inventory; neither replay provenance nor chain applicability now depends on a
  candidate-authored path or unsigned capture claim.
- Required target-local receipts now bind one unique JUnit testcase to every
  lifecycle stage and reject nonzero aggregate suite counters; meta-validation
  remains explicitly diagnostic.
- Rejected candidate `84f7ddeb2c7c1e8c14c9bbf48325f93754627485` after independent review found a fixture-path mismatch and the real exact-diff Agent generated eight executable escapes.
- Repaired self-authored receipts, prose-only unreachability, risk self-downgrade, profile-field injection, stale event digests, source-directory output, torn multi-file snapshots, and absolute evidence paths.
- Rejected `ad783b1` and added manifest/unreachability host attestations, single-component path rejection, contract/candidate/test command binding, and per-stage producer/consumer/assertion bindings.
- Rejected `826c814` and required the attested invocation to include the bound chain test path as an exact argv token; ancestor/source output overlap is also rejected.
- Internally rejected `27316c4`; the command is now constrained to one pytest target plus JUnit, and the checker requires at least one testcase from that module with zero failures, errors, or skips.
- Rejected `6ecd840`; this skill-only iteration now records a host-attested combined-chain unreachability proof instead of claiming a runtime chain, while future HARP runtime targets remain required to execute it. High-risk checker runs also require the externally frozen candidate SHA.
- Rejected `876153f`; unreachability evidence now binds candidate/repository/cwd, and nested workflow/plan/enum maps are strict rather than free-form.
- Rejected `333966b`; candidate-generated causal traces are no longer treated
  as observations, and a clean lexical inventory can no longer grant N/A.
- Rejected `dff8bfb`; the exact Agent-reviewed forward patch and immutable
  candidate checker/validator are now mandatory trusted-runner inputs.
- Rejected `e29ae7d`; lifecycle validation no longer imports a mutable sibling
  after hashing it; the executed module comes directly from the candidate blob.

## Verification evidence

- Pre-change repository HEAD is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- The three source workspaces were inspected read-only and no repair command was executed.
- `pytest -q tests/test_delivery_alignment_contract_checker.py tests/test_delivery_alignment_history_replay.py`: 116 passed after the fifteenth adversarial repair.
- `pytest -q`: 123 passed after the fifteenth adversarial repair.
- `quick_validate.py skills/delivery-alignment-iteration`: `Skill is valid!`.
- `validate_harp_chain_evidence.py` reports all three replay oracles valid. The
  supplemental meta receipt validates only with the explicit diagnostic
  `--allow-meta-validation` flag and cannot satisfy a required runtime gate.
- Durable evidence: `docs/evidence/delivery_alignment_combined_chain_replay_20260801/`.
- `git diff --check`: passed before candidate freeze.

## Adversarial gate evidence

- Risk is high because this changes the canonical skill and checker behavior.
- Base is `d94d282c7982a6de7041343d12df9cee5cf8a7c1`.
- Rejected candidate `84f7dde` had a real Codex exact-diff turn with fingerprint `8c03a4094819a5746cff943aabfd44511e5a7ae552771bb3649f621de33226ce`; it returned eight current attacks, so the gate correctly failed.
- The earlier bubblewrap-blocked turn is retained as diagnostic evidence and is not counted as a gate.
- Candidate `ad783b1` produced six reported attacks; five were repaired. The sixth is the unavoidable fact that a Git commit cannot contain its own SHA and is handled by the post-freeze contract/handoff binding checked against the immutable commit.
- Candidate `826c814` produced one executable attack: a green sibling command could be attested while only hashing an unexecuted failing chain test. The argv-token binding repair closes it.
- Candidate `6ecd840` produced two executable attacks; both are repaired by the honest applicability decision and external candidate binding.
- Candidate `876153f` produced two executable attacks; both are repaired by candidate-bound unreachability evidence and nested-map sanitization.
- Candidate `e606eff` produced two executable attacks; both are repaired by
  current-root predicate re-evaluation and machine-bound handoff candidate metadata.
- Candidate `1269274` produced three executable attacks; they are repaired by
  strict nested assessment scalars, a fixed repository inventory predicate, and
  a separately attested capture witness.
- Candidate `fb93b10` produced two executable attacks; they are repaired by
  package-level signal union and the cross-field blocked-artifact invariant.
- Candidate `ca0359e` produced four executable attacks; they are repaired by
  target-local-only required receipts, the fixed combined-N/A predicate, and
  immutable-diff repository-wide signal union.
- Candidate `258047c` produced two executable attacks; they are repaired by
  immutable candidate-blob applicability and per-stage target-file coverage.
- Candidate `7d13ec8` produced three executable attacks; they are repaired by
  a same-run causal trace plus full candidate-tree and base-deletion inventory.
- Candidate `333966b` produced two executable attacks; they are repaired by an
  external call-boundary observer and an external exact-diff non-HARP scope
  classification.
- Candidate `dff8bfb` produced one executable attack; it is repaired by
  independently freezing the complete forward patch and executing immutable
  candidate checker/validator blobs.
- Candidate `e29ae7d` produced one executable validator-substitution attack; it
  is repaired by in-memory execution of the content-addressed validator blob.
  Sixteenth candidate `09f50941957c849bc12445d233d8f9fd8223c10e` is
  frozen. Its exact-diff Agent review returned zero current executable attacks;
  final trusted attestations and immutable-candidate checker verification pass.

## Open blockers and risks

- No completion blocker remains for this skill iteration.
- A generic evidence validator cannot substitute for a target repository's real producer-to-consumer integration test.
- Existing unrelated untracked files must remain unstaged and unchanged.
- The durable combined receipt is explicitly skill-gate meta-validation; future HARP runtime changes must produce a target-local receipt from their real producers and consumers.

## Exact next action

Apply this skill to the next HARP runtime change: run the real target-local
ten-stage chain with external call-boundary observation and replay the three
sanitized historical archetypes; keep the live source workspaces read-only.

## Final claims allowed now

- This skill iteration is complete for immutable candidate
  `09f50941957c849bc12445d233d8f9fd8223c10e`.
- The skill and checker require additive combined-chain and real-history replay gates for applicable high-risk iterations.
- Three sanitized replay profiles reproduce the distinct observed failure signatures without claiming their live source workspaces are repaired.
- Deterministic implementation, immutable-candidate, forward-patch, and real
  exact-diff Agent gates pass with zero current escaped attacks.
