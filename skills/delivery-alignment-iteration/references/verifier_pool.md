# Verifier Pool: Reusable Proof Tools

Update: 2026-08-06. Companion to `SKILL.md` sections "Verifier pool" and
"Release fast path". The goal is not "proof tools never change" -- it is to
decouple **evolution cost from verification primitives** so that a release
never re-authors (and never re-reviews) a proof tool from scratch.

## 1. Why a pool instead of per-release checkers

The v19 release-bootstrap cycle showed the failure mode: every release wrote a
new 47-path checker, and every new checker was attacked and rejected at T2.5
(authority-root conflation, then TOCTOU / mutable-checkout split). Rewriting a
proof tool per release makes rejection the normal outcome, not the exception.

A verifier pool inverts this: the candidate contributes **data**, the pool
contributes **verified logic**, and only the data is reviewed per release.

## 2. Three layers, isolated by change frequency

| Layer | Changes | Review cost | Example |
|---|---|---|---|
| Parameters | every release | none | base/candidate commits, path list, digests |
| Domain adapters | low frequency (declarations) | light independent review | state schemas, authority map, event types |
| Kernel | very low frequency (logic) | full `gate_tool_upgrade` | git object integrity, TOCTOU-safe reads, signatures |

**Rule:** a new verification need adds a new pool member; it never edits an
accepted member's kernel. A new HARP event type or state object is a schema
declaration (adapter layer), never a kernel change.

## 3. Kernel invariants (what verifiers may rely on)

Every pool member assumes only these stable interfaces from a candidate:

1. `base_commit` and `candidate_commit` resolve in the read-only object store.
2. `path_list` (JSON array) equals the exact diff path set -- no more, no less.
3. `expected_tree` equals `candidate^{tree}`.
4. `expected_patch_sha256` equals the SHA-256 of the deterministic binary
   patch digest algorithm pinned by the verifier version.
5. `contract_hash` (optional binding) equals the SHA-256 of the frozen contract
   bytes.

As long as HARP's evolution preserves these five invariants, every pool member
keeps working without a kernel edit.

## 4. Worked example: `git_integrity_verifier`

Prototype at `report/verifier_demo/git_integrity_verifier.py` (run against the
real r8 repository, 2026-08-05):

- Inputs: `--repo` (read-only object store), `--base`, `--candidate`,
  `--path-list`, `--expected-tree`, `--expected-patch-sha256`.
- Checks C1-C6: objects resolve; `git fsck --strict`; path-list exact; tree
  consistency; patch digest; optional contract binding.
- Demonstrated behavior:
  - correct parameters (candidate `8c853c4`) -> `verdict: pass`;
  - tampered path list (one real path removed) -> `verdict: fail`, reporting
    the exact unexpected path;
  - parameterized reuse (candidate `52f3f5c`, same kernel, new parameters) ->
    `verdict: pass`.

**Why this design removes the v19 P1s structurally:** the verifier reads only
the Git object database and never opens checkout paths, so the
`lstat`->`open` TOCTOU race and the "mutable checkout supplies authority" split
cannot occur; `--repo` names a single read-only object store, so the
authority-root conflation cannot occur. Fixes live in the kernel design, not in
per-release script discipline.

## 4.1 Second member: `state_machine_explorer`

`git_integrity_verifier` answers "are these the bytes you claim". Nothing in the
pool answers "does this state machine have a reachable undefined cell", which is
the question the Canonical Control-State Audit actually asks. That audit's
"bounded model explorer" is required by `SKILL.md` but has had no pool member, so
in practice it was satisfied by prose enumeration.

- **Input (adapter layer, declarative):** a transition table per entity:
  `statuses`, `status_classes` (`open` / `held` / `terminal`), `initial`, and
  legal `(status, event) -> status` cells, plus per-hold `deadline` and
  `on_timeout` declarations.
- **Input (parameters):** the entity set to explore, the reachable
  fault-injection product to consider, and declared unreachability proofs.
- **Kernel checks:**
  - **E1 totality**: no `(reachable status, declared event)` cell is undefined;
    an undefined cell is reported with the witness path from `initial`.
  - **E2 unique result**: replaying duplicate, stale, concurrent,
    partial-write, owner-loss, and restart sequences from each reachable status
    converges to one status, or reports the diverging witness pair.
  - **E3 bounded holds**: every status in class `held` declares a `deadline`
    and an `on_timeout` target that is itself reachable; a held status whose
    timeout target is absent or unreachable is a permanent-freeze witness.
  - **E4 terminal absorption**: no `terminal` status has an outgoing cell
    except through an explicitly declared typed re-open.
  - **E5 taxonomy exclusivity**: every status belongs to exactly one class, and
    no two entities disagree about a shared status name's class.
- **Verdict:** `pass` with the explored state/edge counts, or `fail` naming the
  witness sequence. Witnesses are directly usable as T6 counterexamples and as
  `base_negative` bodies for product fixtures.

Adding an entity or a status is an adapter declaration (light independent
review). Changing E1-E5 semantics is a kernel change under
`gate_tool_upgrade`. A transition table that no explorer consumes does not
satisfy the audit.

## 5. Non-regression fixtures

Every historically confirmed defect becomes a frozen fixture:

```text
verifiers/fixtures/
  reject_52f3f5c_authority_root_conflation/
  reject_8c853c4_toctou_rename_symlink/
  reject_8c853c4_checkout_git_split/
  reject_cli_argument_parse_failure/
  pass_8c853c4_valid_release/
  pass_52f3f5c_valid_release/
  fail_tampered_path_list/
```

Any verifier change (including kernel changes) must pass the full fixture set
before the new version can be pinned. This makes "reviewed once" durable:
regression to a previously fixed defect is machine-blocked forever.

### 5.1 Product-defect fixtures (not only proof-tool fixtures)

The fixture names above are all **proof-tool** defects. That leaves the larger
population (product defects) is protected only by candidate-authored `tests/`,
which `SKILL.md` classifies as an untrusted evidence producer. Regression
protection then rests on the thing the trust rule excludes.

Every closure contributes at least one product fixture:

```text
verifiers/fixtures/product/
  reject_<incident_id>_<defect_class>/
    contract.json        # entity, invariant, oracle
    base_negative.json   # must FAIL on base_commit
    candidate_positive.json  # must PASS on candidate
    replay.json          # pool-member parameters; no candidate code
```

Rules:

1. The fixture is stored outside the candidate repository and replayed by a pool
   member, so a candidate cannot weaken its own regression barrier.
2. `base_negative` must actually fail on the frozen base. A fixture that passes
   on both sides proves nothing and is rejected at T2.5.
3. The fixture names a **defect class**, not a call site. `reject_r25_finalize_
   stale_anchor` is a call site; `reject_identity_resolved_per_consumer` is a
   class. Prefer the class: it is what blocks the sibling-path recurrence.
4. `convergence.product_fixture: not_applicable_with_proof` is allowed only with
   a machine-checked argument that no deterministic oracle exists (for example a
   provider-empirical limit such as a prompt-size cliff).

Fixture accumulation is the mechanism that converts "we fixed it and wrote a
test" into "the class is machine-blocked", and it is the input to the
`root_cause_retirement` credit in `SKILL.md`.

## 6. Upgrade governance

| Change | Path | Cost |
|---|---|---|
| Parameters for a new release | none | ~0 |
| Schema/authority-map declaration | light independent review + fixture subset | low |
| New pool member for a new verification need | single-member R3 review + full fixtures | medium, once |
| Kernel primitive (fix, dependency, new attack surface) | full `gate_tool_upgrade`: external review of new bytes, two independent reviewers, full fixture regression, human accepts new hash | high, rare |

The `gate_tool_upgrade` flow is unchanged from `SKILL.md`; the pool only makes
it rare by moving change to the data and adapter layers.

## 7. Ledger provenance

Every invocation records `verifier_id`, `verifier_version`, `verifier_sha256`,
parameter hashes, and the receipt digest into the external phase ledger, so any
validation is traceable to the exact tool version that produced it.

## 8. Relationship to schema v3

- `release_kind: release_bootstrap` selects the release fast path.
- `verifier_requirements: [{id, version, params}]` names the accepted pool
  members to invoke; the contract does not ship verifier code.
- `budgets.max_consecutive_no_progress_rejections` and
  `budgets.cost_value_threshold` replace the flat candidate-rejection ceiling.
- `convergence.product_fixture` names the fixture this closure contributes and
  the defect classes it retires; `convergence.root_cause_retirement` is the
  machine-counted number of pool fixture classes retired by mechanism removal,
  and feeds the credit clause bounded by `budgets.root_cause_credit_cap`.
- `convergence.sibling_call_sites` carries one disposition per enumerated
  sibling; an unenumerated sibling is an incomplete candidate.
- `risk_profile.reachability_downgrade` requests a one-tier reduction (floor R2)
  and is honored only when it names a pool-member verdict digest proving the
  changed paths are control-unreachable.
- `risk_profile.adds_repair_surface` must be `true` whenever the runner computes
  a positive `repair_surface_delta`.

Production gap list (prototype -> pool): Ed25519-signed receipt chain binding
predecessor authorization; forced external bare-store + root-anchor binding;
canonical patch-digest alignment with historical v10/v18/v19 envelopes;
expanded fixture set covering every archived rejection.
