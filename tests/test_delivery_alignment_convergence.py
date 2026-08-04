from __future__ import annotations

import copy
import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import yaml
import pytest


CHECKER = (
    Path(__file__).parents[1]
    / "skills"
    / "delivery-alignment-iteration"
    / "scripts"
    / "check_iteration_convergence.py"
)
SPEC = importlib.util.spec_from_file_location("iteration_convergence_checker", CHECKER)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

CANDIDATE = "2" * 40


def _contract(tier: str = "R0", *, verifier: Path = CHECKER) -> dict:
    clean_rounds = checker.TIER_CLEAN_ROUNDS[tier]
    authority = tier in {"R2", "R3"}
    blast = {"R0": "local", "R1": "local", "R2": "bounded", "R3": "system"}[
        tier
    ]
    return {
        "schema_version": 3,
        "intent": "Close one frozen test iteration.",
        "non_goals": ["No live mutation."],
        "ssot": [{"path": "README.md", "reason": "fixture"}],
        "deliverables": [
            {"id": "D1", "path": "README.md", "description": "fixture change"}
        ],
        "acceptance_criteria": [
            {"id": "A1", "description": "declared evidence passes"}
        ],
        "verification": [{"id": "V1", "command_or_check": "pytest"}],
        "traceability": [
            {"acceptance": "A1", "deliverables": ["D1"], "verification": ["V1"]}
        ],
        "risks": ["bounded fixture risk"],
        "final_claims_allowed": ["the frozen fixture closes"],
        "handoff": {"path": "docs/handoff.md", "policy": "phase neutral"},
        "trust": {
            "verifier_origin": "installed_skill",
            "verifier_version": checker.POLICY_VERSION,
            "verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(),
            "candidate_tool_role": "untrusted_evidence_producer",
            "candidate_private_signing_material": "forbidden",
            "bootstrap_mode": "normal",
            "root_anchor": {
                "external_signing_public_key_sha256": "b" * 64,
                "base_commit": "1" * 40,
                "contract_hashes": ["c" * 64],
            },
        },
        "threat_model": {
            "frozen": True,
            "protected_assets": ["promotion authority"],
            "attacker_capabilities": ["candidate controls repository bytes"],
            "trusted_components": ["pinned external verifier"],
            "excluded_capabilities": ["host key compromise"],
            "security_properties": [
                {"id": "SP1", "description": "candidate cannot self-authorize"}
            ],
            "evidence_formats": ["strict JSON receipt v1"],
        },
        "risk_profile": {
            "tier": tier,
            "authority_reachability": authority,
            "blast_radius": blast,
            "rationale": "fixture classification",
            "changed_paths": ["README.md"],
            "affected_dependencies": [],
            "required_gates": checker.TIER_GATES[tier],
        },
        "review_policy": {
            "author_id": "author",
            "required_static_reviews": checker.TIER_STATIC_REVIEWS[tier],
            "required_clean_rounds": clean_rounds,
            "max_appeals_per_finding": 1,
            "out_of_model_disposition": "scope_expansion_proposal",
            "criteria_frozen": True,
            "reopen_rule": "signed_property_invalidated",
        },
        "budgets": copy.deepcopy(checker.DEFAULT_BUDGETS),
        "convergence": {
            "acceptance_ids": ["A1"],
            "completeness_required": True,
            "residual_risk_policy": "record_nonblocking_p2_and_provisional",
            "requested_state": "close",
        },
        "phase_ledger": {"mode": "candidate_external", "ledger_id": "fixture-r1"},
    }


def _ledger(contract: dict) -> dict:
    tier = contract["risk_profile"]["tier"]
    model_sha = checker._canonical_sha256(contract["threat_model"])
    gates = {
        name: {"status": "passed", "evidence": f"sha256:{name}"}
        for name in checker.TIER_GATES[tier]
    }
    rounds = []
    for index in range(checker.TIER_CLEAN_ROUNDS[tier]):
        rounds.append(
            {
                "reviewer_id": f"reviewer-{index + 1}",
                "independent": True,
                "candidate": CANDIDATE,
                "threat_model_sha256": model_sha,
                "new_confirmed_blocker_ids": [],
            }
        )
    human_reports = (
        [{"after_review_count": 2, "evidence": "sha256:human-report"}]
        if len(rounds) >= 2
        else []
    )
    last_report = max(
        (row["after_review_count"] for row in human_reports), default=0
    )
    return {
        "schema_version": 1,
        "ledger_id": "fixture-r1",
        "contract_sha256": "pending",
        "base_commit": contract["trust"]["root_anchor"]["base_commit"],
        "candidate_tree": "3" * 40,
        "candidate_patch_sha256": "f" * 64,
        "actual_changed_paths": contract["risk_profile"]["changed_paths"],
        "candidate": CANDIDATE,
        "threat_model_sha256": model_sha,
        "verifier_sha256": contract["trust"]["verifier_sha256"],
        "acceptance_results": [
            {"id": "A1", "passed": True, "evidence": "sha256:acceptance"}
        ],
        "gate_results": gates,
        "findings": [],
        "review_rounds": rounds,
        "completeness_map": [
            {
                "path": "README.md",
                "disposition": "changed_and_verified",
                "proof": "V1",
            }
        ],
        "residual_risks": [],
        "static_review_receipts": [],
        "budget_usage": {
            "candidate_rejections": 0,
            "adversarial_rounds": len(rounds),
            "new_attacks_by_round": [0] * len(rounds),
            "active_engineering_hours": 1,
            "candidate_reviews_since_human_report": len(rounds) - last_report,
            "human_reports": human_reports,
        },
    }


def _host_key(tmp_path: Path) -> tuple[Path, Path]:
    trust_root = tmp_path / "host-trust"
    trust_root.mkdir(exist_ok=True)
    private_key = trust_root / "ledger-private.pem"
    public_key = trust_root / "ledger-public.pem"
    subprocess_commands = [
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private_key)],
        [
            "openssl",
            "pkey",
            "-in",
            str(private_key),
            "-pubout",
            "-out",
            str(public_key),
        ],
    ]
    for command in subprocess_commands:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return private_key, public_key


def _sign_ledger(ledger: dict, private_key: Path, tmp_path: Path) -> None:
    ledger.pop("attestation", None)
    payload = checker._canonical_ledger_payload(ledger)
    payload_path = tmp_path / "ledger-payload.json"
    signature_path = tmp_path / "ledger-signature.bin"
    payload_path.write_bytes(payload)
    subprocess.run(
        [
            "openssl",
            "pkeyutl",
            "-sign",
            "-inkey",
            str(private_key),
            "-rawin",
            "-in",
            str(payload_path),
            "-out",
            str(signature_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ledger["attestation"] = {
        "algorithm": "ed25519",
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "signature_base64": base64.b64encode(signature_path.read_bytes()).decode(),
    }


def _freeze_repo(candidate_root: Path, contract: dict, ledger: dict) -> None:
    subprocess.run(["git", "init", "-q"], cwd=candidate_root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=candidate_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=candidate_root, check=True
    )
    readme = candidate_root / "README.md"
    readme.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=candidate_root, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=candidate_root, check=True)
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=candidate_root, text=True
    ).strip()
    readme.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=candidate_root, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "candidate"], cwd=candidate_root, check=True
    )
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=candidate_root, text=True
    ).strip()
    tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=candidate_root, text=True
    ).strip()
    patch = subprocess.check_output(
        ["git", "diff", "--binary", "--full-index", base, candidate, "--"],
        cwd=candidate_root,
    )
    paths = sorted(
        subprocess.check_output(
            ["git", "diff", "--name-only", base, candidate, "--"],
            cwd=candidate_root,
            text=True,
        ).splitlines()
    )
    contract["trust"]["root_anchor"]["base_commit"] = base
    contract["risk_profile"]["changed_paths"] = paths
    ledger["base_commit"] = base
    ledger["candidate"] = candidate
    ledger["candidate_tree"] = tree
    ledger["candidate_patch_sha256"] = hashlib.sha256(patch).hexdigest()
    ledger["actual_changed_paths"] = paths
    ledger["threat_model_sha256"] = checker._canonical_sha256(
        contract["threat_model"]
    )
    for row in ledger.get("review_rounds", []):
        row["candidate"] = candidate
        row["threat_model_sha256"] = ledger["threat_model_sha256"]
    for finding in ledger.get("findings", []):
        if finding.get("exact_candidate_identity") == CANDIDATE:
            finding["exact_candidate_identity"] = candidate


def _trusted_bare(candidate_root: Path, tmp_path: Path) -> Path:
    trust_root = tmp_path / "host-trust"
    trust_root.mkdir(exist_ok=True)
    index = 1
    trusted_git_dir = trust_root / f"candidate-{index}.git"
    while trusted_git_dir.exists():
        index += 1
        trusted_git_dir = trust_root / f"candidate-{index}.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", str(trusted_git_dir)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    source_objects = candidate_root / ".git" / "objects"
    target_objects = trusted_git_dir / "objects"
    for source in source_objects.iterdir():
        if source.name == "info":
            continue
        target = target_objects / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
    return trusted_git_dir


def _bind_contract_and_sign(
    contract: dict,
    ledger: dict,
    *,
    contract_path: Path,
    private_key: Path,
    public_key: Path,
    tmp_path: Path,
) -> None:
    contract["trust"]["root_anchor"]["external_signing_public_key_sha256"] = (
        hashlib.sha256(public_key.read_bytes()).hexdigest()
    )
    contract_path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
    ledger["contract_sha256"] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    ledger["base_commit"] = contract["trust"]["root_anchor"]["base_commit"]
    review_root = tmp_path / "static-reviews"
    review_root.mkdir(exist_ok=True)
    receipts = []
    for index in range(contract["review_policy"]["required_static_reviews"]):
        report_path = review_root / f"review-{index + 1}.md"
        report_path.write_text(
            f"accepted static exact-diff review {index + 1}\n", encoding="utf-8"
        )
        receipts.append(
            {
                "reviewer_id": f"static-reviewer-{index + 1}",
                "independent": True,
                "verdict": "accepted",
                "review_object": "static_exact_diff",
                "candidate": ledger["candidate"],
                "candidate_tree": ledger["candidate_tree"],
                "candidate_patch_sha256": ledger["candidate_patch_sha256"],
                "contract_sha256": ledger["contract_sha256"],
                "verifier_sha256": ledger["verifier_sha256"],
                "report_path": str(report_path.resolve()),
                "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
                "reviewed_at_utc": f"2026-08-04T00:00:0{index}Z",
            }
        )
    ledger["static_review_receipts"] = receipts
    _sign_ledger(ledger, private_key, tmp_path)


def _evaluate(
    tmp_path: Path,
    contract: dict,
    ledger: dict,
    *,
    verifier=CHECKER,
    accepted_verifier_sha256: str = "",
    expected_root_anchor_sha256: str = "",
    evaluation_phase: str = "closure",
    static_review_receipts_override: list[dict] | None = None,
    poison_candidate_git: bool = False,
):
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir(parents=True, exist_ok=True)
    _freeze_repo(candidate_root, contract, ledger)
    if poison_candidate_git:
        sentinel = tmp_path / "candidate-git-executed"
        malicious_driver = candidate_root / "malicious-diff-driver.py"
        malicious_driver.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            f"Path({str(sentinel)!r}).touch()\n",
            encoding="utf-8",
        )
        malicious_driver.chmod(0o755)
        subprocess.run(
            ["git", "config", "diff.external", str(malicious_driver)],
            cwd=candidate_root,
            check=True,
        )
    trusted_git_dir = _trusted_bare(candidate_root, tmp_path)
    private_key, public_key = _host_key(tmp_path)
    contract_path = tmp_path / "contract.yaml"
    ledger_path = tmp_path / "external-ledger.json"
    _bind_contract_and_sign(
        contract,
        ledger,
        contract_path=contract_path,
        private_key=private_key,
        public_key=public_key,
        tmp_path=tmp_path,
    )
    if static_review_receipts_override is not None:
        ledger["static_review_receipts"] = static_review_receipts_override
        _sign_ledger(ledger, private_key, tmp_path)
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    contract_sha = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    root_anchor_sha = checker._canonical_sha256(contract["trust"]["root_anchor"])
    return checker.evaluate(
        contract,
        ledger,
        contract_path=contract_path,
        ledger_path=ledger_path,
        candidate_root=candidate_root,
        trusted_git_dir=trusted_git_dir,
        verifier_path=verifier,
        public_key_path=public_key,
        expected_root_anchor_sha256=(
            expected_root_anchor_sha256 or root_anchor_sha
        ),
        expected_contract_sha256=contract_sha,
        expected_verifier_sha256=contract["trust"]["verifier_sha256"],
        expected_prior_verifier_sha256=str(
            contract["trust"].get("prior_verifier_sha256") or ""
        ),
        accepted_verifier_sha256=accepted_verifier_sha256,
        evaluation_phase=evaluation_phase,
    )


def test_r0_closes_without_full_gate_or_adversarial_round(tmp_path: Path) -> None:
    contract = _contract("R0")
    result = _evaluate(tmp_path, contract, _ledger(contract))
    assert result["decision"] == "close", result
    assert set(_ledger(contract)["gate_results"]) == {"static"}


def test_r3_requires_and_closes_after_two_distinct_clean_rounds(tmp_path: Path) -> None:
    contract = _contract("R3")
    ledger = _ledger(contract)
    assert _evaluate(tmp_path, contract, ledger)["decision"] == "close"
    ledger["review_rounds"][-1]["new_confirmed_blocker_ids"] = ["F-new"]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "continue"
    assert any("review tail" in reason for reason in result["closure_reasons"])


def test_pre_execution_requires_bound_static_review_receipts(tmp_path: Path) -> None:
    contract = _contract("R2")
    ledger = _ledger(contract)
    accepted = _evaluate(
        tmp_path / "accepted",
        contract,
        ledger,
        evaluation_phase="pre_execution",
    )
    assert accepted["decision"] == "authorize_execution", accepted

    missing_contract = _contract("R2")
    missing = _evaluate(
        tmp_path / "missing",
        missing_contract,
        _ledger(missing_contract),
        evaluation_phase="pre_execution",
        static_review_receipts_override=[],
    )
    assert missing["decision"] == "invalid", missing
    assert any("exactly 1 receipts" in error for error in missing["errors"])


def test_candidate_git_config_cannot_influence_freeze_recomputation(
    tmp_path: Path,
) -> None:
    contract = _contract("R1")
    result = _evaluate(
        tmp_path,
        contract,
        _ledger(contract),
        poison_candidate_git=True,
    )
    assert result["decision"] == "close", result
    assert not (tmp_path / "candidate-git-executed").exists()


def test_out_of_model_reviewer_requirement_cannot_block_current_candidate(
    tmp_path: Path,
) -> None:
    contract = _contract("R1")
    ledger = _ledger(contract)
    ledger["findings"] = [
        {
            "id": "F-out",
            "status": "provisional",
            "severity": "P1",
            "reviewer_id": "reviewer-1",
            "violated_predeclared_property": "NEW_PROPERTY",
            "attacker_capability": "invented capability",
        }
    ]
    ledger["residual_risks"] = [{"finding_id": "F-out", "disposition": "next_iteration"}]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "close", result


def test_mislabeled_out_of_model_p1_becomes_nonblocking_scope_proposal(
    tmp_path: Path,
) -> None:
    contract = _contract("R1")
    ledger = _ledger(contract)
    ledger["findings"] = [
        {
            "id": "F-out",
            "status": "confirmed_open",
            "severity": "P1",
            "reviewer_id": "reviewer-1",
            "violated_predeclared_property": "NEW_PROPERTY",
            "attacker_capability": "invented capability",
            "exact_candidate_identity": CANDIDATE,
            "deterministic_counterexample_or_static_proof": "static proof",
            "authority_boundary_crossed": True,
            "remediation_scope": "unfrozen/file.py",
            "appeals": [],
        }
    ]
    ledger["residual_risks"] = [
        {"finding_id": "F-out", "disposition": "scope_expansion_proposal"}
    ]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "close", result


def test_confirmed_in_model_p1_blocks_closure(tmp_path: Path) -> None:
    contract = _contract("R2")
    ledger = _ledger(contract)
    ledger["findings"] = [
        {
            "id": "F1",
            "status": "confirmed_open",
            "severity": "P1",
            "reviewer_id": "reviewer-1",
            "violated_predeclared_property": "SP1",
            "attacker_capability": "candidate controls repository bytes",
            "exact_candidate_identity": CANDIDATE,
            "deterministic_counterexample_or_static_proof": "pytest::test_repro",
            "authority_boundary_crossed": True,
            "remediation_scope": "README.md",
            "appeals": [],
        }
    ]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "continue"
    assert result["blocking_findings"] == ["F1"]


def test_budget_exhaustion_forces_human_checkpoint(tmp_path: Path) -> None:
    contract = _contract("R3")
    ledger = _ledger(contract)
    ledger["budget_usage"]["human_reports"] = []
    ledger["budget_usage"]["candidate_reviews_since_human_report"] = 2
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "human_checkpoint"
    assert "periodic human report is due" in result["human_checkpoints"]


def test_candidate_contained_verifier_cannot_close_normal_iteration(
    tmp_path: Path,
) -> None:
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir()
    candidate_checker = candidate_root / "checker.py"
    shutil.copy2(CHECKER, candidate_checker)
    contract = _contract("R0", verifier=candidate_checker)
    ledger = _ledger(contract)
    _freeze_repo(candidate_root, contract, ledger)
    trusted_git_dir = _trusted_bare(candidate_root, tmp_path)
    private_key, public_key = _host_key(tmp_path)
    contract_path = tmp_path / "contract.yaml"
    ledger_path = tmp_path / "external-ledger.json"
    _bind_contract_and_sign(
        contract,
        ledger,
        contract_path=contract_path,
        private_key=private_key,
        public_key=public_key,
        tmp_path=tmp_path,
    )
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    result = checker.evaluate(
        contract,
        ledger,
        contract_path=contract_path,
        ledger_path=ledger_path,
        candidate_root=candidate_root,
        trusted_git_dir=trusted_git_dir,
        verifier_path=candidate_checker,
        public_key_path=public_key,
        expected_root_anchor_sha256=checker._canonical_sha256(
            contract["trust"]["root_anchor"]
        ),
        expected_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        expected_verifier_sha256=contract["trust"]["verifier_sha256"],
    )
    assert result["decision"] == "invalid"
    assert any("verifier must resolve outside" in error for error in result["errors"])


def test_gate_tool_upgrade_can_only_be_ready_for_external_acceptance(
    tmp_path: Path,
) -> None:
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir()
    candidate_checker = candidate_root / "checker.py"
    shutil.copy2(CHECKER, candidate_checker)
    contract = _contract("R0", verifier=candidate_checker)
    contract["trust"]["bootstrap_mode"] = "gate_tool_upgrade"
    contract["trust"]["prior_verifier_sha256"] = "e" * 64
    ledger = _ledger(contract)
    _freeze_repo(candidate_root, contract, ledger)
    trusted_git_dir = _trusted_bare(candidate_root, tmp_path)
    private_key, public_key = _host_key(tmp_path)
    contract_path = tmp_path / "contract.yaml"
    ledger_path = tmp_path / "external-ledger.json"
    _bind_contract_and_sign(
        contract,
        ledger,
        contract_path=contract_path,
        private_key=private_key,
        public_key=public_key,
        tmp_path=tmp_path,
    )
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    result = checker.evaluate(
        contract,
        ledger,
        contract_path=contract_path,
        ledger_path=ledger_path,
        candidate_root=candidate_root,
        trusted_git_dir=trusted_git_dir,
        verifier_path=candidate_checker,
        public_key_path=public_key,
        expected_root_anchor_sha256=checker._canonical_sha256(
            contract["trust"]["root_anchor"]
        ),
        expected_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        expected_verifier_sha256=contract["trust"]["verifier_sha256"],
        expected_prior_verifier_sha256=contract["trust"]["prior_verifier_sha256"],
    )
    assert result["decision"] == "ready_for_external_acceptance", result
    assert not result["closed"]


def test_external_copy_of_unaccepted_gate_tool_still_cannot_close(
    tmp_path: Path,
) -> None:
    contract = _contract("R0", verifier=CHECKER)
    contract["trust"]["bootstrap_mode"] = "gate_tool_upgrade"
    contract["trust"]["prior_verifier_sha256"] = "e" * 64
    result = _evaluate(tmp_path / "pending", contract, _ledger(contract))
    assert result["decision"] == "ready_for_external_acceptance", result

    accepted_contract = _contract("R0", verifier=CHECKER)
    accepted_contract["trust"]["bootstrap_mode"] = "gate_tool_upgrade"
    accepted_contract["trust"]["prior_verifier_sha256"] = "e" * 64
    accepted_hash = accepted_contract["trust"]["verifier_sha256"]
    accepted = _evaluate(
        tmp_path / "accepted",
        accepted_contract,
        _ledger(accepted_contract),
        accepted_verifier_sha256=accepted_hash,
    )
    assert accepted["decision"] == "close", accepted


def test_candidate_declared_root_cannot_replace_host_expected_anchor(
    tmp_path: Path,
) -> None:
    contract = _contract("R0")
    result = _evaluate(
        tmp_path,
        contract,
        _ledger(contract),
        expected_root_anchor_sha256="0" * 64,
    )
    assert result["decision"] == "invalid"
    assert any("host-expected" in error for error in result["errors"])


def test_rejected_independent_appeal_releases_reviewer_veto(tmp_path: Path) -> None:
    contract = _contract("R1")
    ledger = _ledger(contract)
    ledger["findings"] = [
        {
            "id": "F1",
            "status": "confirmed_open",
            "severity": "P1",
            "reviewer_id": "reviewer-1",
            "violated_predeclared_property": "SP1",
            "attacker_capability": "candidate controls repository bytes",
            "exact_candidate_identity": CANDIDATE,
            "deterministic_counterexample_or_static_proof": "static proof",
            "authority_boundary_crossed": True,
            "remediation_scope": "README.md",
            "appeals": [
                {"adjudicator_id": "adjudicator-2", "decision": "rejected"}
            ],
        }
    ]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "close", result


def test_author_cannot_adjudicate_appeal_against_independent_blocker(
    tmp_path: Path,
) -> None:
    contract = _contract("R1")
    ledger = _ledger(contract)
    ledger["findings"] = [
        {
            "id": "F1",
            "status": "confirmed_open",
            "severity": "P1",
            "reviewer_id": "reviewer-1",
            "violated_predeclared_property": "SP1",
            "attacker_capability": "candidate controls repository bytes",
            "exact_candidate_identity": CANDIDATE,
            "deterministic_counterexample_or_static_proof": "static proof",
            "authority_boundary_crossed": True,
            "remediation_scope": "README.md",
            "appeals": [{"adjudicator_id": "author", "decision": "rejected"}],
        }
    ]
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "invalid", result
    assert any("independent of author" in error for error in result["errors"])


def test_phase_ledger_inside_candidate_is_rejected(tmp_path: Path) -> None:
    contract = _contract("R0")
    ledger = _ledger(contract)
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir()
    _freeze_repo(candidate_root, contract, ledger)
    trusted_git_dir = _trusted_bare(candidate_root, tmp_path)
    private_key, public_key = _host_key(tmp_path)
    contract_path = tmp_path / "contract.yaml"
    ledger_path = candidate_root / "phase-ledger.json"
    _bind_contract_and_sign(
        contract,
        ledger,
        contract_path=contract_path,
        private_key=private_key,
        public_key=public_key,
        tmp_path=tmp_path,
    )
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    result = checker.evaluate(
        contract,
        ledger,
        contract_path=contract_path,
        ledger_path=ledger_path,
        candidate_root=candidate_root,
        trusted_git_dir=trusted_git_dir,
        verifier_path=CHECKER,
        public_key_path=public_key,
        expected_root_anchor_sha256=checker._canonical_sha256(
            contract["trust"]["root_anchor"]
        ),
        expected_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        expected_verifier_sha256=contract["trust"]["verifier_sha256"],
    )
    assert result["decision"] == "invalid"
    assert any("phase ledger must resolve outside" in error for error in result["errors"])


def test_candidate_private_signing_material_is_forbidden(tmp_path: Path) -> None:
    contract = _contract("R0")
    contract["trust"]["candidate_private_signing_material"] = "available"
    result = _evaluate(tmp_path, contract, _ledger(contract))
    assert result["decision"] == "invalid"
    assert any("private_signing_material" in error for error in result["errors"])


def test_phase_ledger_tamper_after_host_signature_is_rejected(tmp_path: Path) -> None:
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir()
    contract = _contract("R0")
    ledger = _ledger(contract)
    _freeze_repo(candidate_root, contract, ledger)
    trusted_git_dir = _trusted_bare(candidate_root, tmp_path)
    private_key, public_key = _host_key(tmp_path)
    contract_path = tmp_path / "contract.yaml"
    ledger_path = tmp_path / "external-ledger.json"
    _bind_contract_and_sign(
        contract,
        ledger,
        contract_path=contract_path,
        private_key=private_key,
        public_key=public_key,
        tmp_path=tmp_path,
    )
    ledger["acceptance_results"][0]["evidence"] = "tampered-after-signing"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    result = checker.evaluate(
        contract,
        ledger,
        contract_path=contract_path,
        ledger_path=ledger_path,
        candidate_root=candidate_root,
        trusted_git_dir=trusted_git_dir,
        verifier_path=CHECKER,
        public_key_path=public_key,
        expected_root_anchor_sha256=checker._canonical_sha256(
            contract["trust"]["root_anchor"]
        ),
        expected_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        expected_verifier_sha256=contract["trust"]["verifier_sha256"],
    )
    assert result["decision"] == "invalid"
    assert any("payload digest is invalid" in error for error in result["errors"])


def test_completeness_accepts_verified_unchanged_dependency(tmp_path: Path) -> None:
    contract = _contract("R1")
    contract["risk_profile"]["affected_dependencies"] = ["docs/spec.md"]
    ledger = _ledger(contract)
    ledger["completeness_map"].append(
        {
            "path": "docs/spec.md",
            "disposition": "unchanged_dependency_verified",
            "proof": "V1",
        }
    )
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "close", result


def test_changed_path_cannot_claim_unchanged_dependency_disposition(
    tmp_path: Path,
) -> None:
    contract = _contract("R1")
    ledger = _ledger(contract)
    ledger["completeness_map"][0]["disposition"] = "unchanged_dependency_verified"
    result = _evaluate(tmp_path, contract, ledger)
    assert result["decision"] == "invalid"
    assert any("changed path" in error for error in result["errors"])


def test_duplicate_json_ledger_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker._load_json(path)
