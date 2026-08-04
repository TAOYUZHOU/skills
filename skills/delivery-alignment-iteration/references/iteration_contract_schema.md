# Iteration Contract Schema v3

Use strict YAML for every new iteration contract. Schema v1/v2 and
`check_delivery_contract.py` are retained only to read and audit historical
evidence; they cannot authorize a new candidate.

Schema v3 separates four objects that older contracts conflated:

1. the immutable candidate and its phase-neutral handoff;
2. the frozen threat/risk/acceptance contract;
3. the candidate-external, pinned verifier TCB; and
4. the mutable candidate-external phase ledger.

The normative trust sequence, risk tiers, admissible findings, budgets, appeal
rule, and closure formula are in
[`trust_and_convergence.md`](trust_and_convergence.md).

## Contract fields

Common delivery fields:

- `schema_version`: literal integer `3`.
- `intent`: one observable iteration outcome.
- `non_goals`: explicit exclusions.
- `ssot`: authoritative paths/sources and reasons.
- `deliverables`: stable IDs, paths/objects, and descriptions.
- `acceptance_criteria`: stable IDs and observable conditions.
- `verification`: stable IDs and exact commands/checks.
- `traceability`: acceptance-to-deliverable-to-verification mapping.
- `risks`: known risks before execution.
- `final_claims_allowed`: bounded claims permitted only after closure.
- `handoff`: stable candidate-tree path and phase-neutral update policy.

Trust fields:

- `trust.verifier_origin`: exactly `installed_skill`.
- `trust.verifier_version`: exactly `trust-convergence-v1` for this schema.
- `trust.verifier_sha256`: SHA-256 of the executing external verifier.
- `trust.candidate_tool_role`: exactly `untrusted_evidence_producer`.
- `trust.candidate_private_signing_material`: exactly `forbidden`.
- `trust.bootstrap_mode`: `normal` or `gate_tool_upgrade`.
- `trust.prior_verifier_sha256`: required for `gate_tool_upgrade`.
- `trust.root_anchor.external_signing_public_key_sha256`: public verification
  anchor. Private key material and its path are never candidate inputs.
- `trust.root_anchor.base_commit`: immutable base SHA.
- `trust.root_anchor.contract_hashes`: immutable hashes accepted at T0.

Threat-model fields:

- `threat_model.frozen`: exactly `true`. The verifier computes its canonical
  digest; the signed T2 ledger binds that digest to the exact candidate.
- `protected_assets`, `attacker_capabilities`, `trusted_components`,
  `excluded_capabilities`, and `evidence_formats`: explicit lists.
- `security_properties`: stable `{id, description}` records. Only these
  properties can support an ordinary current-candidate blocking P0/P1.

Risk fields:

- `risk_profile.tier`: `R0`, `R1`, `R2`, or `R3`.
- `authority_reachability`: boolean; `true` cannot be lower than R2.
- `blast_radius`: `local`, `bounded`, `system`, or `release`.
- `rationale`: authority/blast-radius justification.
- `changed_paths`: complete expected Git diff path set.
- `affected_dependencies`: unchanged dependencies whose contracts must be
  reverified; may be empty and must not overlap `changed_paths`.
- `required_gates`: the exact ordered tier gate set below.

```yaml
R0: [static]
R1: [static, targeted_regression, independent_review_1]
R2: [static, targeted_regression, atomic_boundary,
  combined_chain_if_reachable, historical_replay_if_reachable,
  independent_adversarial_1]
R3: [static, targeted_regression, atomic_boundary,
  combined_chain_if_reachable, historical_replay_if_reachable, host_tcb,
  independent_adversarial_1, independent_adversarial_2, full_dynamic]
```

Review, budget, and closure fields:

- `review_policy.author_id`: candidate author identity.
- `required_static_reviews`: R0 `0`, R1/R2 `1`, R3 `2`; every accepted
  T2.5 receipt must be from a distinct reviewer who is not the author.
- `required_clean_rounds`: R0 `0`, R1/R2 `1`, R3 `2`.
- `max_appeals_per_finding`: exactly `1`.
- `out_of_model_disposition`: exactly `scope_expansion_proposal`.
- `criteria_frozen`: exactly `true`.
- `reopen_rule`: exactly `signed_property_invalidated`.
- `budgets`: every field shown below; values may be stricter but not looser
  without explicit human approval.
- `convergence.acceptance_ids`: exact acceptance ID set.
- `completeness_required`: exactly `true`.
- `residual_risk_policy`: exactly
  `record_nonblocking_p2_and_provisional`.
- `requested_state`: `open` or `close`.
- `phase_ledger.mode`: exactly `candidate_external`.
- `phase_ledger.ledger_id`: stable ledger identity, not a candidate path.

## Full contract example

```yaml
schema_version: 3
intent: "Make one bounded parser change without widening promotion authority."
non_goals:
  - "No state-machine or release change."
ssot:
  - path: docs/parser_contract.md
    reason: "Accepted parser semantics."
deliverables:
  - id: D1
    path: src/parser.py
    description: "Bounded parser correction."
acceptance_criteria:
  - id: A1
    description: "The incident payload parses to the declared typed result."
verification:
  - id: V1
    command_or_check: "pytest -q tests/test_parser.py"
traceability:
  - acceptance: A1
    deliverables: [D1]
    verification: [V1]
risks:
  - "Malformed neighbor payload remains fail closed."
final_claims_allowed:
  - "The frozen parser case and declared neighbors pass."
handoff:
  path: docs/iteration_handoff.md
  policy: "Phase-neutral candidate truth; freeze at T2."
trust:
  verifier_origin: installed_skill
  verifier_version: trust-convergence-v1
  verifier_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  candidate_tool_role: untrusted_evidence_producer
  candidate_private_signing_material: forbidden
  bootstrap_mode: normal
  root_anchor:
    external_signing_public_key_sha256: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    base_commit: "1111111111111111111111111111111111111111"
    contract_hashes:
      - "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
threat_model:
  frozen: true
  protected_assets: ["typed parser decision"]
  attacker_capabilities: ["supplies malformed bounded payload"]
  trusted_components: ["pinned external verifier"]
  excluded_capabilities: ["host verifier compromise"]
  security_properties:
    - id: SP1
      description: "Malformed payload cannot authorize a typed decision."
  evidence_formats: ["strict JSON receipt v1"]
risk_profile:
  tier: R2
  authority_reachability: true
  blast_radius: bounded
  rationale: "The parser output crosses one decision boundary."
  changed_paths: [src/parser.py, tests/test_parser.py]
  affected_dependencies: [docs/parser_contract.md]
  required_gates: [static, targeted_regression, atomic_boundary,
    combined_chain_if_reachable, historical_replay_if_reachable,
    independent_adversarial_1]
review_policy:
  author_id: primary-agent
  required_static_reviews: 1
  required_clean_rounds: 1
  max_appeals_per_finding: 1
  out_of_model_disposition: scope_expansion_proposal
  criteria_frozen: true
  reopen_rule: signed_property_invalidated
budgets:
  max_candidate_rejections: 2
  max_adversarial_rounds_per_candidate: 2
  max_new_attacks_per_round: 8
  max_active_engineering_hours_without_checkpoint: 4
  human_report_every_candidate_reviews: 2
  max_appeals_per_finding: 1
convergence:
  acceptance_ids: [A1]
  completeness_required: true
  residual_risk_policy: record_nonblocking_p2_and_provisional
  requested_state: open
phase_ledger:
  mode: candidate_external
  ledger_id: parser-iteration-r1
```

## External phase ledger

The ledger is strict JSON stored outside the candidate repository. Minimum
shape:

```json
{
  "schema_version": 1,
  "ledger_id": "parser-iteration-r1",
  "contract_sha256": "<SHA-256 of the exact schema-v3 contract bytes>",
  "base_commit": "1111111111111111111111111111111111111111",
  "candidate_tree": "3333333333333333333333333333333333333333",
  "candidate_patch_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "actual_changed_paths": ["src/parser.py", "tests/test_parser.py"],
  "candidate": "2222222222222222222222222222222222222222",
  "threat_model_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "verifier_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "acceptance_results": [
    {"id": "A1", "passed": true, "evidence": "sha256:..."}
  ],
  "gate_results": {
    "static": {"status": "passed", "evidence": "sha256:..."},
    "targeted_regression": {"status": "passed", "evidence": "sha256:..."},
    "atomic_boundary": {"status": "passed", "evidence": "sha256:..."},
    "combined_chain_if_reachable": {
      "status": "not_applicable",
      "unreachability_proof": "sha256:..."
    },
    "historical_replay_if_reachable": {
      "status": "not_applicable",
      "unreachability_proof": "sha256:..."
    },
    "independent_adversarial_1": {
      "status": "passed",
      "evidence": "sha256:..."
    }
  },
  "findings": [],
  "review_rounds": [
    {
      "reviewer_id": "independent-reviewer-1",
      "independent": true,
      "candidate": "2222222222222222222222222222222222222222",
      "threat_model_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "new_confirmed_blocker_ids": []
    }
  ],
  "completeness_map": [
    {
      "path": "src/parser.py",
      "disposition": "changed_and_verified",
      "proof": "V1"
    },
    {
      "path": "tests/test_parser.py",
      "disposition": "changed_and_verified",
      "proof": "V1"
    },
    {
      "path": "docs/parser_contract.md",
      "disposition": "unchanged_dependency_verified",
      "proof": "static contract comparison"
    }
  ],
  "residual_risks": [],
  "static_review_receipts": [
    {
      "reviewer_id": "static-reviewer-1",
      "independent": true,
      "verdict": "accepted",
      "review_object": "static_exact_diff",
      "candidate": "2222222222222222222222222222222222222222",
      "candidate_tree": "3333333333333333333333333333333333333333",
      "candidate_patch_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "contract_sha256": "<SHA-256 of the exact schema-v3 contract bytes>",
      "verifier_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "report_path": "/external/reviews/static-review-1.md",
      "report_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "reviewed_at_utc": "2026-08-04T00:00:00Z"
    }
  ],
  "budget_usage": {
    "candidate_rejections": 0,
    "adversarial_rounds": 1,
    "new_attacks_by_round": [3],
    "active_engineering_hours": 2,
    "candidate_reviews_since_human_report": 1,
    "human_reports": []
  },
  "attestation": {
    "algorithm": "ed25519",
    "payload_sha256": "<SHA-256 of canonical ledger JSON without attestation>",
    "signature_base64": "<64-byte detached signature in base64>"
  }
}
```

## Finding records

Allowed statuses are `confirmed_open`, `resolved`, `provisional`, and
`rejected`; severities are P0/P1/P2. A current blocking finding contains:

```json
{
  "id": "F1",
  "status": "confirmed_open",
  "severity": "P1",
  "reviewer_id": "reviewer-1",
  "violated_predeclared_property": "SP1",
  "attacker_capability": "supplies malformed bounded payload",
  "exact_candidate_identity": "2222222222222222222222222222222222222222",
  "deterministic_counterexample_or_static_proof": "pytest::test_repro",
  "authority_boundary_crossed": true,
  "remediation_scope": "src/parser.py",
  "appeals": []
}
```

Without every proof field or in-model IDs, use `provisional`/P2 and add the
finding to `residual_risks`. The reviewer must differ from
`review_policy.author_id`. One appeal has an `adjudicator_id` distinct from both
the reviewer and author and decision `upheld`, `rejected`, or `downgraded`; it
cannot add a new criterion. `rejected` releases the original veto and
`downgraded` requires a residual-risk entry.

## Evaluator outcomes

The host signs canonical UTF-8 JSON (sorted keys, compact separators) with the
top-level `attestation` field omitted. The verifier uses the candidate-external
public key passed with `--public-key` and requires its file hash to equal
`trust.root_anchor.external_signing_public_key_sha256`.

The CLI additionally requires `--trusted-git-dir`, a host-prepared
candidate-external bare object store, plus host-supplied expected hashes for the
verifier, root anchor, and exact contract bytes. Git runs with replacement
objects, external diff/text conversion, hooks, and user/system configuration
disabled. `gate_tool_upgrade` also requires the host-expected prior verifier.
Copying a new verifier outside the candidate does not accept it: without
`--accepted-verifier-sha256` the evaluator returns only
`ready_for_external_acceptance`; after explicit acceptance the host may pass the
new hash and request closure.

`check_iteration_convergence.py` returns:

- `invalid`: schema, identity, trust, finding, or ledger contradiction;
- `authorize_execution`: `--phase pre_execution` verified the frozen Git
  identity and the exact tier-required accepted T2.5 receipts;
- `continue`: valid iteration with unsatisfied closure conditions;
- `human_checkpoint`: budget or adjudicated emergency requires a person;
- `ready_for_external_acceptance`: a gate-tool upgrade passed diagnostics but
  its candidate-contained new verifier cannot authorize itself;
- `close`: the pinned external verifier proved the finite closure formula.

Use `--require-close` for product promotion. Never treat
`ready_for_external_acceptance` as product closure.

## Handoff format

The stable Markdown handoff includes nonempty metadata `status`,
`updated_at_utc`, `iteration`, `contract`, and frozen `candidate`, plus sections
for intent, non-goals, current truth, phase-neutral candidate instructions,
completed changes, verification evidence, residual risks, allowed claims, and
exact next action. Post-freeze reviewer turns and phase changes belong only in
the external ledger.
