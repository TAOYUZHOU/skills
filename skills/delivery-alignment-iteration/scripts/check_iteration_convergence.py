#!/usr/bin/env python3
"""Evaluate a finite schema-v3 iteration contract and external phase ledger."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


POLICY_VERSION = "trust-convergence-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TIERS = {"R0", "R1", "R2", "R3"}
TIER_CLEAN_ROUNDS = {"R0": 0, "R1": 1, "R2": 1, "R3": 2}
TIER_GATES = {
    "R0": ["static"],
    "R1": ["static", "targeted_regression", "independent_review_1"],
    "R2": [
        "static",
        "targeted_regression",
        "atomic_boundary",
        "combined_chain_if_reachable",
        "historical_replay_if_reachable",
        "independent_adversarial_1",
    ],
    "R3": [
        "static",
        "targeted_regression",
        "atomic_boundary",
        "combined_chain_if_reachable",
        "historical_replay_if_reachable",
        "host_tcb",
        "independent_adversarial_1",
        "independent_adversarial_2",
        "full_dynamic",
    ],
}
COMMON_REQUIRED = {
    "intent",
    "non_goals",
    "ssot",
    "deliverables",
    "acceptance_criteria",
    "verification",
    "traceability",
    "risks",
    "final_claims_allowed",
    "handoff",
}
V3_REQUIRED = {
    "trust",
    "threat_model",
    "risk_profile",
    "review_policy",
    "budgets",
    "convergence",
    "phase_ledger",
}
TRUST_REQUIRED = {
    "verifier_origin",
    "verifier_version",
    "verifier_sha256",
    "candidate_tool_role",
    "candidate_private_signing_material",
    "bootstrap_mode",
    "root_anchor",
}
THREAT_REQUIRED = {
    "frozen",
    "protected_assets",
    "attacker_capabilities",
    "trusted_components",
    "excluded_capabilities",
    "security_properties",
    "evidence_formats",
}
FINDING_PROOF_FIELDS = {
    "violated_predeclared_property",
    "attacker_capability",
    "exact_candidate_identity",
    "deterministic_counterexample_or_static_proof",
    "authority_boundary_crossed",
    "remediation_scope",
}
COMPLETENESS_DISPOSITIONS = {
    "changed_and_verified",
    "unchanged_dependency_verified",
    "not_applicable_with_proof",
}
DEFAULT_BUDGETS = {
    "max_candidate_rejections": 2,
    "max_adversarial_rounds_per_candidate": 2,
    "max_new_attacks_per_round": 8,
    "max_active_engineering_hours_without_checkpoint": 4,
    "human_report_every_candidate_reviews": 2,
    "max_appeals_per_finding": 1,
}
LEDGER_REQUIRED = {
    "schema_version",
    "ledger_id",
    "contract_sha256",
    "base_commit",
    "candidate",
    "candidate_tree",
    "candidate_patch_sha256",
    "actual_changed_paths",
    "threat_model_sha256",
    "verifier_sha256",
    "acceptance_results",
    "gate_results",
    "findings",
    "review_rounds",
    "completeness_map",
    "residual_risks",
    "budget_usage",
    "attestation",
}


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_yaml(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    data = yaml.load(raw.decode("utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError("contract must be a YAML mapping")
    return data, raw


def _reject_duplicate_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str):
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    data = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_json_pairs,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(data, dict):
        raise ValueError("phase ledger must be a JSON mapping")
    return data, raw


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _git_text(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout


def _git_bytes(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            completed.stderr.decode(errors="replace").strip()
            or f"git {' '.join(args)} failed"
        )
    return completed.stdout


def _canonical_ledger_payload(ledger: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in ledger.items() if key != "attestation"}
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _verify_ledger_attestation(
    ledger: dict[str, Any], public_key_bytes: bytes
) -> tuple[bool, str]:
    attestation = ledger.get("attestation")
    if not isinstance(attestation, dict):
        return False, "phase ledger attestation must be a mapping"
    if set(attestation) != {"algorithm", "payload_sha256", "signature_base64"}:
        return False, "phase ledger attestation fields are invalid"
    if attestation.get("algorithm") != "ed25519":
        return False, "phase ledger attestation algorithm must be ed25519"
    payload = _canonical_ledger_payload(ledger)
    payload_sha = hashlib.sha256(payload).hexdigest()
    if attestation.get("payload_sha256") != payload_sha:
        return False, "phase ledger attestation payload digest is invalid"
    try:
        signature = base64.b64decode(
            str(attestation.get("signature_base64") or ""), validate=True
        )
    except (ValueError, TypeError):
        return False, "phase ledger attestation signature is not valid base64"
    if len(signature) != 64:
        return False, "phase ledger Ed25519 signature must be 64 bytes"
    try:
        with tempfile.TemporaryDirectory(prefix="iteration-ledger-verify-") as raw:
            temp_root = Path(raw)
            payload_path = temp_root / "payload.json"
            signature_path = temp_root / "signature.bin"
            public_key_path = temp_root / "public-key.pem"
            payload_path.write_bytes(payload)
            signature_path.write_bytes(signature)
            public_key_path.write_bytes(public_key_bytes)
            completed = subprocess.run(
                [
                    "openssl",
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(public_key_path),
                    "-rawin",
                    "-in",
                    str(payload_path),
                    "-sigfile",
                    str(signature_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
    except OSError as exc:
        return False, f"cannot run Ed25519 verifier: {exc}"
    if completed.returncode != 0:
        return False, "phase ledger Ed25519 signature is invalid"
    return True, ""


def _nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _required_mapping(
    value: Any,
    required: set[str],
    label: str,
    errors: list[str],
    *,
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return {}
    missing = sorted(required - set(value))
    if missing:
        errors.append(f"{label} missing fields: {', '.join(missing)}")
    unexpected = sorted(set(value) - required - (optional or set()))
    if unexpected:
        errors.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    for key in sorted(required & set(value)):
        if isinstance(value[key], bool):
            continue
        if not _nonempty(value[key]) and key != "excluded_capabilities":
            errors.append(f"{label}.{key} must be nonempty")
    return value


def _record_list(
    value: Any,
    *,
    label: str,
    required: set[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a nonempty list")
        return []
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be a mapping")
            continue
        missing = sorted(required - set(item))
        unexpected = sorted(set(item) - required)
        if missing:
            errors.append(
                f"{label}[{index}] missing fields: {', '.join(missing)}"
            )
        if unexpected:
            errors.append(
                f"{label}[{index}] has unexpected fields: {', '.join(unexpected)}"
            )
        for key in required & set(item):
            if not _nonempty(item[key]):
                errors.append(f"{label}[{index}].{key} must be nonempty")
        records.append(item)
    return records


def _string_list(value: Any, label: str, errors: list[str], *, empty_ok=False) -> list[str]:
    if not isinstance(value, list) or (not value and not empty_ok):
        errors.append(f"{label} must be {'a' if empty_ok else 'a nonempty'} list")
        return []
    if not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{label} must contain only nonempty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} must not contain duplicates")
    return value


def _property_ids(value: Any, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append("threat_model.security_properties must be a nonempty list")
        return set()
    ids: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"security_properties[{index}] must be a mapping")
            continue
        identifier = item.get("id")
        description = item.get("description")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"security_properties[{index}].id must be nonempty")
        elif not isinstance(description, str) or not description.strip():
            errors.append(
                f"security_properties[{index}].description must be nonempty"
            )
        else:
            ids.append(identifier)
    if len(ids) != len(set(ids)):
        errors.append("threat_model.security_properties IDs must be unique")
    return set(ids)


def validate_contract(contract: dict[str, Any], verifier_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if contract.get("schema_version") != 3:
        errors.append("schema_version must be integer 3")
    for field in sorted(COMMON_REQUIRED | V3_REQUIRED):
        if field not in contract:
            errors.append(f"missing top-level field: {field}")
        elif not _nonempty(contract[field]):
            errors.append(f"empty top-level field: {field}")

    allowed_top_level = {"schema_version"} | COMMON_REQUIRED | V3_REQUIRED
    unexpected_top_level = sorted(set(contract) - allowed_top_level)
    if unexpected_top_level:
        errors.append(
            "unexpected top-level fields: " + ", ".join(unexpected_top_level)
        )
    if not isinstance(contract.get("intent"), str) or not contract.get("intent", "").strip():
        errors.append("intent must be a nonempty string")
    for field in ("non_goals", "risks", "final_claims_allowed"):
        _string_list(contract.get(field), field, errors)
    _record_list(
        contract.get("ssot"),
        label="ssot",
        required={"path", "reason"},
        errors=errors,
    )
    deliverables = _record_list(
        contract.get("deliverables"),
        label="deliverables",
        required={"id", "path", "description"},
        errors=errors,
    )
    acceptance = _record_list(
        contract.get("acceptance_criteria"),
        label="acceptance_criteria",
        required={"id", "description"},
        errors=errors,
    )
    verification = _record_list(
        contract.get("verification"),
        label="verification",
        required={"id", "command_or_check"},
        errors=errors,
    )
    traceability = _record_list(
        contract.get("traceability"),
        label="traceability",
        required={"acceptance", "deliverables", "verification"},
        errors=errors,
    )
    identifier_sets: dict[str, set[str]] = {}
    for label, rows in (
        ("deliverables", deliverables),
        ("acceptance_criteria", acceptance),
        ("verification", verification),
    ):
        identifiers = [str(row.get("id") or "") for row in rows]
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"{label} IDs must be unique")
        identifier_sets[label] = set(identifiers)
    traced_acceptance: set[str] = set()
    for index, row in enumerate(traceability):
        acceptance_id = str(row.get("acceptance") or "")
        traced_acceptance.add(acceptance_id)
        if acceptance_id not in identifier_sets["acceptance_criteria"]:
            errors.append(f"traceability[{index}] references unknown acceptance")
        for field, target in (
            ("deliverables", "deliverables"),
            ("verification", "verification"),
        ):
            values = _string_list(
                row.get(field), f"traceability[{index}].{field}", errors
            )
            if not set(values).issubset(identifier_sets[target]):
                errors.append(f"traceability[{index}] references unknown {field}")
    if (
        traced_acceptance != identifier_sets["acceptance_criteria"]
        or len(traceability) != len(identifier_sets["acceptance_criteria"])
    ):
        errors.append("traceability must cover every acceptance criterion exactly")
    handoff = _required_mapping(
        contract.get("handoff"), {"path", "policy"}, "handoff", errors
    )
    handoff_path = str(handoff.get("path") or "")
    if handoff and (
        Path(handoff_path).is_absolute()
        or ".." in Path(handoff_path).parts
        or not handoff_path.startswith("docs/")
    ):
        errors.append("handoff.path must be a contained repository docs path")

    trust = _required_mapping(
        contract.get("trust"),
        TRUST_REQUIRED,
        "trust",
        errors,
        optional={"prior_verifier_sha256"},
    )
    if trust:
        if trust.get("verifier_origin") != "installed_skill":
            errors.append("trust.verifier_origin must be installed_skill")
        if trust.get("verifier_version") != POLICY_VERSION:
            errors.append(f"trust.verifier_version must be {POLICY_VERSION}")
        actual_verifier_sha = _sha256_file(verifier_path)
        if trust.get("verifier_sha256") != actual_verifier_sha:
            errors.append("trust.verifier_sha256 does not match executing verifier")
        if trust.get("candidate_tool_role") != "untrusted_evidence_producer":
            errors.append(
                "trust.candidate_tool_role must be untrusted_evidence_producer"
            )
        if trust.get("candidate_private_signing_material") != "forbidden":
            errors.append(
                "trust.candidate_private_signing_material must be forbidden"
            )
        if trust.get("bootstrap_mode") not in {"normal", "gate_tool_upgrade"}:
            errors.append("trust.bootstrap_mode must be normal or gate_tool_upgrade")
        if trust.get("bootstrap_mode") == "gate_tool_upgrade" and not SHA256_RE.fullmatch(
            str(trust.get("prior_verifier_sha256") or "")
        ):
            errors.append(
                "gate_tool_upgrade requires trust.prior_verifier_sha256"
            )
        if (
            trust.get("bootstrap_mode") == "normal"
            and "prior_verifier_sha256" in trust
        ):
            errors.append("normal mode must not declare trust.prior_verifier_sha256")
        anchor = _required_mapping(
            trust.get("root_anchor"),
            {
                "external_signing_public_key_sha256",
                "base_commit",
                "contract_hashes",
            },
            "trust.root_anchor",
            errors,
        )
        if anchor:
            if not SHA256_RE.fullmatch(
                str(anchor.get("external_signing_public_key_sha256") or "")
            ):
                errors.append(
                    "trust.root_anchor.external_signing_public_key_sha256 must be SHA-256"
                )
            if not COMMIT_RE.fullmatch(str(anchor.get("base_commit") or "")):
                errors.append("trust.root_anchor.base_commit must be a commit SHA")
            hashes = _string_list(
                anchor.get("contract_hashes"),
                "trust.root_anchor.contract_hashes",
                errors,
            )
            if any(not SHA256_RE.fullmatch(item) for item in hashes):
                errors.append("trust.root_anchor.contract_hashes must be SHA-256 values")

    threat = _required_mapping(
        contract.get("threat_model"), THREAT_REQUIRED, "threat_model", errors
    )
    property_ids: set[str] = set()
    attacker_capabilities: set[str] = set()
    threat_model_sha256 = ""
    if threat:
        if threat.get("frozen") is not True:
            errors.append("threat_model.frozen must be true")
        threat_model_sha256 = _canonical_sha256(threat)
        for field in (
            "protected_assets",
            "trusted_components",
            "evidence_formats",
        ):
            _string_list(threat.get(field), f"threat_model.{field}", errors)
        attacker_capabilities = set(
            _string_list(
                threat.get("attacker_capabilities"),
                "threat_model.attacker_capabilities",
                errors,
            )
        )
        _string_list(
            threat.get("excluded_capabilities"),
            "threat_model.excluded_capabilities",
            errors,
            empty_ok=True,
        )
        property_ids = _property_ids(threat.get("security_properties"), errors)

    risk = _required_mapping(
        contract.get("risk_profile"),
        {
            "tier",
            "authority_reachability",
            "blast_radius",
            "rationale",
            "changed_paths",
            "required_gates",
        },
        "risk_profile",
        errors,
    )
    tier = str(risk.get("tier") or "")
    changed_paths: list[str] = []
    if risk:
        if tier not in TIERS:
            errors.append("risk_profile.tier must be R0, R1, R2, or R3")
        if type(risk.get("authority_reachability")) is not bool:
            errors.append("risk_profile.authority_reachability must be boolean")
        if risk.get("blast_radius") not in {"local", "bounded", "system", "release"}:
            errors.append(
                "risk_profile.blast_radius must be local, bounded, system, or release"
            )
        changed_paths = _string_list(
            risk.get("changed_paths"), "risk_profile.changed_paths", errors
        )
        gates = _string_list(
            risk.get("required_gates"), "risk_profile.required_gates", errors
        )
        if tier in TIER_GATES and gates != TIER_GATES[tier]:
            errors.append(
                f"risk_profile.required_gates must equal the ordered {tier} gate set"
            )
        if risk.get("authority_reachability") is True and tier in {"R0", "R1"}:
            errors.append("authority-reachable changes cannot be classified below R2")

    review = _required_mapping(
        contract.get("review_policy"),
        {
            "author_id",
            "required_clean_rounds",
            "max_appeals_per_finding",
            "out_of_model_disposition",
            "criteria_frozen",
            "reopen_rule",
        },
        "review_policy",
        errors,
    )
    if review:
        if tier in TIER_CLEAN_ROUNDS and review.get("required_clean_rounds") != TIER_CLEAN_ROUNDS[tier]:
            errors.append(
                f"review_policy.required_clean_rounds must be {TIER_CLEAN_ROUNDS.get(tier)} for {tier}"
            )
        if review.get("max_appeals_per_finding") != 1:
            errors.append("review_policy.max_appeals_per_finding must be 1")
        if review.get("out_of_model_disposition") != "scope_expansion_proposal":
            errors.append(
                "review_policy.out_of_model_disposition must be scope_expansion_proposal"
            )
        if review.get("criteria_frozen") is not True:
            errors.append("review_policy.criteria_frozen must be true")
        if review.get("reopen_rule") != "signed_property_invalidated":
            errors.append(
                "review_policy.reopen_rule must be signed_property_invalidated"
            )

    budgets = _required_mapping(
        contract.get("budgets"), set(DEFAULT_BUDGETS), "budgets", errors
    )
    if budgets:
        for field, default in DEFAULT_BUDGETS.items():
            value = budgets.get(field)
            if type(value) not in {int, float} or value <= 0:
                errors.append(f"budgets.{field} must be positive")
            elif value > default:
                errors.append(
                    f"budgets.{field} may be stricter but cannot exceed default {default}"
                )

    convergence = _required_mapping(
        contract.get("convergence"),
        {
            "acceptance_ids",
            "completeness_required",
            "residual_risk_policy",
            "requested_state",
        },
        "convergence",
        errors,
    )
    if convergence:
        acceptance_ids = _string_list(
            convergence.get("acceptance_ids"),
            "convergence.acceptance_ids",
            errors,
        )
        declared_acceptance = {
            str(item.get("id"))
            for item in contract.get("acceptance_criteria", [])
            if isinstance(item, dict) and item.get("id")
        }
        if set(acceptance_ids) != declared_acceptance:
            errors.append(
                "convergence.acceptance_ids must match declared acceptance criteria"
            )
        if convergence.get("completeness_required") is not True:
            errors.append("convergence.completeness_required must be true")
        if (
            convergence.get("residual_risk_policy")
            != "record_nonblocking_p2_and_provisional"
        ):
            errors.append("convergence.residual_risk_policy is invalid")
        if convergence.get("requested_state") not in {"open", "close"}:
            errors.append("convergence.requested_state must be open or close")

    phase = _required_mapping(
        contract.get("phase_ledger"), {"mode", "ledger_id"}, "phase_ledger", errors
    )
    if phase and phase.get("mode") != "candidate_external":
        errors.append("phase_ledger.mode must be candidate_external")

    return {
        "ok": not errors,
        "errors": errors,
        "tier": tier,
        "property_ids": sorted(property_ids),
        "attacker_capabilities": sorted(attacker_capabilities),
        "changed_paths": changed_paths,
        "threat_model_sha256": threat_model_sha256,
        "verifier_sha256": _sha256_file(verifier_path),
    }


def _validate_finding(
    finding: Any,
    index: int,
    *,
    candidate: str,
    property_ids: set[str],
    capabilities: set[str],
    max_appeals: int,
    errors: list[str],
) -> tuple[str, bool, bool]:
    label = f"findings[{index}]"
    if not isinstance(finding, dict):
        errors.append(f"{label} must be a mapping")
        return "", False, False
    finding_id = finding.get("id")
    status = finding.get("status")
    severity = finding.get("severity")
    if not isinstance(finding_id, str) or not finding_id.strip():
        errors.append(f"{label}.id must be nonempty")
        finding_id = ""
    if status not in {"confirmed_open", "resolved", "provisional", "rejected"}:
        errors.append(f"{label}.status is invalid")
    if severity not in {"P0", "P1", "P2"}:
        errors.append(f"{label}.severity is invalid")

    appeals = finding.get("appeals", [])
    if not isinstance(appeals, list):
        errors.append(f"{label}.appeals must be a list")
        appeals = []
    if len(appeals) > max_appeals:
        errors.append(f"{label} exceeds the one-appeal limit")
    reviewer_id = str(finding.get("reviewer_id") or "")
    for appeal_index, appeal in enumerate(appeals):
        if not isinstance(appeal, dict):
            errors.append(f"{label}.appeals[{appeal_index}] must be a mapping")
            continue
        if appeal.get("decision") not in {"upheld", "rejected", "downgraded"}:
            errors.append(f"{label}.appeals[{appeal_index}].decision is invalid")
        if not str(appeal.get("adjudicator_id") or "").strip():
            errors.append(f"{label}.appeals[{appeal_index}].adjudicator_id is empty")
        elif appeal.get("adjudicator_id") == reviewer_id:
            errors.append(f"{label} appeal adjudicator must be independent")

    emergency = finding.get("emergency_reopen") is True
    blocking = status == "confirmed_open" and severity in {"P0", "P1"}
    if blocking:
        for field in sorted(FINDING_PROOF_FIELDS):
            if field not in finding or not _nonempty(finding[field]):
                errors.append(f"{label}.{field} is required for a blocking finding")
        if finding.get("authority_boundary_crossed") is not True:
            errors.append(f"{label}.authority_boundary_crossed must be true")
        in_model = (
            finding.get("violated_predeclared_property") in property_ids
            and finding.get("attacker_capability") in capabilities
        )
        if not in_model:
            if not (
                emergency
                and severity == "P0"
                and finding.get("emergency_adjudication") == "upheld"
            ):
                errors.append(
                    f"{label} is out of model and must be provisional or an adjudicated emergency P0"
                )
                blocking = False
        if finding.get("exact_candidate_identity") != candidate:
            errors.append(f"{label}.exact_candidate_identity does not match ledger")
    return str(finding_id), blocking, emergency and blocking


def evaluate(
    contract: dict[str, Any],
    ledger: dict[str, Any],
    *,
    contract_path: Path,
    ledger_path: Path,
    candidate_root: Path,
    verifier_path: Path,
    public_key_path: Path,
    contract_bytes: bytes | None = None,
    ledger_bytes: bytes | None = None,
    public_key_bytes: bytes | None = None,
) -> dict[str, Any]:
    contract_result = validate_contract(contract, verifier_path)
    errors = list(contract_result["errors"])
    closure_reasons: list[str] = []
    checkpoints: list[str] = []
    trust = contract.get("trust") if isinstance(contract.get("trust"), dict) else {}

    ledger_fields = set(ledger)
    missing_ledger_fields = sorted(LEDGER_REQUIRED - ledger_fields)
    unexpected_ledger_fields = sorted(ledger_fields - LEDGER_REQUIRED)
    if missing_ledger_fields:
        errors.append(
            "phase ledger missing fields: " + ", ".join(missing_ledger_fields)
        )
    if unexpected_ledger_fields:
        errors.append(
            "phase ledger has unexpected fields: "
            + ", ".join(unexpected_ledger_fields)
        )

    try:
        ledger_path.resolve().relative_to(candidate_root.resolve())
    except ValueError:
        ledger_external = True
    else:
        ledger_external = False
        errors.append("phase ledger must resolve outside the candidate repository")

    try:
        public_key_path.resolve().relative_to(candidate_root.resolve())
    except ValueError:
        public_key_external = True
    else:
        public_key_external = False
        errors.append("verification public key must resolve outside the candidate repository")
    try:
        bound_public_key_bytes = (
            public_key_bytes if public_key_bytes is not None else public_key_path.read_bytes()
        )
    except OSError as exc:
        bound_public_key_bytes = b""
        errors.append(f"cannot read verification public key: {exc}")
    public_key_sha = hashlib.sha256(bound_public_key_bytes).hexdigest()
    expected_public_key_sha = str(
        ((trust.get("root_anchor") or {}).get("external_signing_public_key_sha256") or "")
        if isinstance(trust.get("root_anchor"), dict)
        else ""
    )
    if public_key_sha != expected_public_key_sha:
        errors.append("verification public key does not match the root anchor")
    attestation_ok, attestation_error = _verify_ledger_attestation(
        ledger, bound_public_key_bytes
    )
    if not attestation_ok:
        errors.append(attestation_error)

    bootstrap_mode = trust.get("bootstrap_mode")
    try:
        verifier_path.resolve().relative_to(candidate_root.resolve())
    except ValueError:
        verifier_external = True
    else:
        verifier_external = False
        if bootstrap_mode != "gate_tool_upgrade":
            errors.append("verifier must resolve outside the candidate repository")

    phase = contract.get("phase_ledger") if isinstance(contract.get("phase_ledger"), dict) else {}
    if ledger.get("schema_version") != 1:
        errors.append("phase ledger schema_version must be integer 1")
    if ledger.get("ledger_id") != phase.get("ledger_id"):
        errors.append("phase ledger ID does not match contract")
    bound_contract_bytes = (
        contract_bytes if contract_bytes is not None else contract_path.read_bytes()
    )
    bound_ledger_bytes = ledger_bytes if ledger_bytes is not None else ledger_path.read_bytes()
    contract_sha = hashlib.sha256(bound_contract_bytes).hexdigest()
    if ledger.get("contract_sha256") != contract_sha:
        errors.append("phase ledger contract hash does not match contract bytes")
    anchor = trust.get("root_anchor") if isinstance(trust.get("root_anchor"), dict) else {}
    base_commit = str(anchor.get("base_commit") or "")
    if ledger.get("base_commit") != base_commit:
        errors.append("phase ledger base commit does not match root anchor")
    candidate_patch_sha = str(ledger.get("candidate_patch_sha256") or "")
    if not SHA256_RE.fullmatch(candidate_patch_sha):
        errors.append("phase ledger candidate_patch_sha256 must be SHA-256")
    candidate_tree = str(ledger.get("candidate_tree") or "")
    if not COMMIT_RE.fullmatch(candidate_tree):
        errors.append("phase ledger candidate_tree must be a tree SHA")
    actual_changed_paths = ledger.get("actual_changed_paths")
    if not isinstance(actual_changed_paths, list) or not all(
        isinstance(path, str) and path.strip() for path in actual_changed_paths
    ):
        errors.append("phase ledger actual_changed_paths must be nonempty strings")
    elif actual_changed_paths != contract_result["changed_paths"]:
        errors.append("phase ledger actual changed paths do not match risk profile")

    candidate = str(ledger.get("candidate") or "")
    if not COMMIT_RE.fullmatch(candidate):
        errors.append("phase ledger candidate must be a commit SHA")
    if ledger.get("threat_model_sha256") != contract_result["threat_model_sha256"]:
        errors.append("phase ledger threat-model hash does not match contract")
    if ledger.get("verifier_sha256") != contract_result["verifier_sha256"]:
        errors.append("phase ledger verifier hash does not match executing verifier")
    if COMMIT_RE.fullmatch(base_commit) and COMMIT_RE.fullmatch(candidate):
        try:
            resolved_base = _git_text(
                candidate_root, "rev-parse", f"{base_commit}^{{commit}}"
            ).strip()
            resolved_candidate = _git_text(
                candidate_root, "rev-parse", f"{candidate}^{{commit}}"
            ).strip()
            ancestry = subprocess.run(
                ["git", "merge-base", "--is-ancestor", resolved_base, resolved_candidate],
                cwd=candidate_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if ancestry.returncode != 0:
                errors.append("phase ledger candidate must descend from base")
            actual_tree = _git_text(
                candidate_root, "rev-parse", f"{resolved_candidate}^{{tree}}"
            ).strip()
            git_paths = sorted(
                path
                for path in _git_text(
                    candidate_root,
                    "diff",
                    "--name-only",
                    resolved_base,
                    resolved_candidate,
                    "--",
                ).splitlines()
                if path
            )
            git_patch_sha = hashlib.sha256(
                _git_bytes(
                    candidate_root,
                    "diff",
                    "--binary",
                    "--full-index",
                    resolved_base,
                    resolved_candidate,
                    "--",
                )
            ).hexdigest()
            if actual_tree != candidate_tree:
                errors.append("phase ledger candidate tree does not match Git object")
            if git_paths != actual_changed_paths:
                errors.append("phase ledger changed paths do not match Git diff")
            if git_patch_sha != candidate_patch_sha:
                errors.append("phase ledger candidate patch does not match Git diff")
            try:
                relative_contract = contract_path.resolve().relative_to(
                    candidate_root.resolve()
                )
            except ValueError:
                relative_contract = None
            if relative_contract is not None:
                candidate_contract = _git_bytes(
                    candidate_root,
                    "show",
                    f"{resolved_candidate}:{relative_contract.as_posix()}",
                )
                if candidate_contract != bound_contract_bytes:
                    errors.append(
                        "contract bytes do not match the immutable candidate object"
                    )
        except ValueError as exc:
            errors.append(f"cannot recompute Git freeze binding: {exc}")

    acceptance_ids = set((contract.get("convergence") or {}).get("acceptance_ids") or [])
    acceptance_results = ledger.get("acceptance_results")
    passed_acceptance: set[str] = set()
    if not isinstance(acceptance_results, list):
        errors.append("phase ledger acceptance_results must be a list")
    else:
        for index, row in enumerate(acceptance_results):
            if not isinstance(row, dict):
                errors.append(f"acceptance_results[{index}] must be a mapping")
                continue
            identifier = row.get("id")
            if identifier not in acceptance_ids:
                errors.append(f"acceptance_results[{index}] has unknown ID")
            if row.get("passed") is True and _nonempty(row.get("evidence")):
                passed_acceptance.add(str(identifier))
        missing_acceptance = sorted(acceptance_ids - passed_acceptance)
        if missing_acceptance:
            closure_reasons.append(
                "acceptance criteria not passed: " + ", ".join(missing_acceptance)
            )

    risk = contract.get("risk_profile") if isinstance(contract.get("risk_profile"), dict) else {}
    required_gates = list(risk.get("required_gates") or [])
    gate_results = ledger.get("gate_results")
    if not isinstance(gate_results, dict):
        errors.append("phase ledger gate_results must be a mapping")
        gate_results = {}
    for gate_name in required_gates:
        gate = gate_results.get(gate_name)
        if not isinstance(gate, dict):
            closure_reasons.append(f"missing gate result: {gate_name}")
            continue
        status = gate.get("status")
        if status == "passed" and _nonempty(gate.get("evidence")):
            continue
        if (
            gate_name.endswith("_if_reachable")
            and status == "not_applicable"
            and _nonempty(gate.get("unreachability_proof"))
        ):
            continue
        closure_reasons.append(f"gate not satisfied: {gate_name}")

    findings = ledger.get("findings")
    if not isinstance(findings, list):
        errors.append("phase ledger findings must be a list")
        findings = []
    finding_ids: list[str] = []
    blockers: list[str] = []
    emergency = False
    max_appeals = int((contract.get("review_policy") or {}).get("max_appeals_per_finding") or 0)
    for index, finding in enumerate(findings):
        identifier, blocking, emergency_blocker = _validate_finding(
            finding,
            index,
            candidate=candidate,
            property_ids=set(contract_result["property_ids"]),
            capabilities=set(contract_result["attacker_capabilities"]),
            max_appeals=max_appeals,
            errors=errors,
        )
        finding_ids.append(identifier)
        if blocking:
            blockers.append(identifier)
        emergency = emergency or emergency_blocker
    if len(finding_ids) != len(set(finding_ids)):
        errors.append("finding IDs must be unique")
    if blockers:
        closure_reasons.append("unresolved confirmed P0/P1: " + ", ".join(blockers))
    if emergency:
        checkpoints.append("adjudicated out-of-model emergency P0 requires a new freeze")

    residual_risks = ledger.get("residual_risks")
    if not isinstance(residual_risks, list):
        errors.append("phase ledger residual_risks must be a list")
        residual_ids: set[str] = set()
    else:
        residual_ids = {
            str(row.get("finding_id"))
            for row in residual_risks
            if isinstance(row, dict) and row.get("finding_id")
        }
    required_residuals = {
        str(row.get("id"))
        for row in findings
        if isinstance(row, dict)
        and row.get("status") in {"provisional", "confirmed_open"}
        and row.get("severity") == "P2"
    }
    required_residuals.update(
        str(row.get("id"))
        for row in findings
        if isinstance(row, dict) and row.get("status") == "provisional"
    )
    if not required_residuals.issubset(residual_ids):
        closure_reasons.append("provisional/P2 findings missing from residual-risk register")

    changed_paths = set(contract_result["changed_paths"])
    completeness = ledger.get("completeness_map")
    mapped_paths: set[str] = set()
    if not isinstance(completeness, list):
        errors.append("phase ledger completeness_map must be a list")
    else:
        for index, row in enumerate(completeness):
            if not isinstance(row, dict):
                errors.append(f"completeness_map[{index}] must be a mapping")
                continue
            path = row.get("path")
            disposition = row.get("disposition")
            proof = row.get("proof")
            if path not in changed_paths:
                errors.append(f"completeness_map[{index}] has undeclared path")
            elif path in mapped_paths:
                errors.append(f"completeness_map duplicates path: {path}")
            else:
                mapped_paths.add(str(path))
            if disposition not in COMPLETENESS_DISPOSITIONS:
                errors.append(f"completeness_map[{index}].disposition is invalid")
            if not _nonempty(proof):
                errors.append(f"completeness_map[{index}].proof must be nonempty")
    missing_paths = sorted(changed_paths - mapped_paths)
    if missing_paths:
        closure_reasons.append("missing completeness mappings: " + ", ".join(missing_paths))

    review_policy = contract.get("review_policy") if isinstance(contract.get("review_policy"), dict) else {}
    required_rounds = int(review_policy.get("required_clean_rounds") or 0)
    author_id = str(review_policy.get("author_id") or "")
    review_rounds = ledger.get("review_rounds")
    if not isinstance(review_rounds, list):
        errors.append("phase ledger review_rounds must be a list")
        review_rounds = []
    tail = review_rounds[-required_rounds:] if required_rounds else []
    clean_reviewers: list[str] = []
    if len(tail) < required_rounds:
        closure_reasons.append(
            f"requires {required_rounds} consecutive independent clean review rounds"
        )
    else:
        for index, row in enumerate(tail):
            if not isinstance(row, dict):
                closure_reasons.append("clean review tail contains a malformed round")
                continue
            reviewer = str(row.get("reviewer_id") or "")
            clean = (
                row.get("independent") is True
                and reviewer
                and reviewer != author_id
                and row.get("candidate") == candidate
                and row.get("threat_model_sha256")
                == contract_result["threat_model_sha256"]
                and row.get("new_confirmed_blocker_ids") == []
            )
            if not clean:
                closure_reasons.append(
                    f"review tail round {index + 1} is not independent and clean"
                )
            clean_reviewers.append(reviewer)
        if len(clean_reviewers) != len(set(clean_reviewers)):
            closure_reasons.append("required clean rounds must use distinct reviewers")

    budgets = contract.get("budgets") if isinstance(contract.get("budgets"), dict) else {}
    usage = ledger.get("budget_usage")
    if not isinstance(usage, dict):
        errors.append("phase ledger budget_usage must be a mapping")
        usage = {}
    numeric_checks = {
        "candidate_rejections": "max_candidate_rejections",
        "adversarial_rounds": "max_adversarial_rounds_per_candidate",
        "active_engineering_hours": "max_active_engineering_hours_without_checkpoint",
    }
    for usage_key, budget_key in numeric_checks.items():
        value = usage.get(usage_key)
        if type(value) not in {int, float} or value < 0:
            errors.append(f"budget_usage.{usage_key} must be nonnegative")
        elif value > budgets.get(budget_key, 0):
            checkpoints.append(f"budget exhausted: {budget_key}")
    review_count = usage.get("candidate_reviews_since_human_report")
    if type(review_count) is not int or review_count < 0:
        errors.append(
            "budget_usage.candidate_reviews_since_human_report must be nonnegative integer"
        )
    elif review_count >= budgets.get("human_report_every_candidate_reviews", 0):
        checkpoints.append("periodic human report is due")
    attacks_by_round = usage.get("new_attacks_by_round")
    if not isinstance(attacks_by_round, list) or not all(
        type(value) is int and value >= 0 for value in attacks_by_round
    ):
        errors.append("budget_usage.new_attacks_by_round must be nonnegative integers")
    elif any(
        value > budgets.get("max_new_attacks_per_round", 0)
        for value in attacks_by_round
    ):
        checkpoints.append("budget exhausted: max_new_attacks_per_round")

    if errors:
        decision = "invalid"
    elif checkpoints:
        decision = "human_checkpoint"
    elif closure_reasons:
        decision = "continue"
    elif bootstrap_mode == "gate_tool_upgrade" and not verifier_external:
        decision = "ready_for_external_acceptance"
    else:
        decision = "close"

    return {
        "ok": not errors,
        "closed": decision == "close",
        "decision": decision,
        "errors": errors,
        "closure_reasons": closure_reasons,
        "human_checkpoints": checkpoints,
        "trust": {
            "policy_version": POLICY_VERSION,
            "verifier_path": str(verifier_path.resolve()),
            "verifier_sha256": contract_result["verifier_sha256"],
            "verifier_external_to_candidate": verifier_external,
            "bootstrap_mode": bootstrap_mode,
            "ledger_external_to_candidate": ledger_external,
            "public_key_external_to_candidate": public_key_external,
            "public_key_sha256": public_key_sha,
            "ledger_attestation_valid": attestation_ok,
        },
        "identity": {
            "contract_path": str(contract_path.resolve()),
            "contract_sha256": contract_sha,
            "ledger_path": str(ledger_path.resolve()),
            "ledger_sha256": hashlib.sha256(bound_ledger_bytes).hexdigest(),
            "candidate": candidate,
            "candidate_tree": candidate_tree,
            "candidate_patch_sha256": candidate_patch_sha,
            "threat_model_sha256": contract_result["threat_model_sha256"],
        },
        "blocking_findings": blockers,
        "required_clean_rounds": required_rounds,
        "observed_review_rounds": len(review_rounds),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument(
        "--public-key",
        required=True,
        help="Candidate-external Ed25519 public key used to verify the phase ledger.",
    )
    parser.add_argument(
        "--expected-verifier-sha256",
        help="Optional root-anchor hash supplied by the host runner.",
    )
    parser.add_argument("--require-close", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    contract_path = Path(args.contract).resolve()
    ledger_path = Path(args.ledger).resolve()
    verifier_path = Path(__file__).resolve()
    try:
        contract, contract_bytes = _load_yaml(contract_path)
        ledger, ledger_bytes = _load_json(ledger_path)
        public_key_path = Path(args.public_key).resolve()
        public_key_bytes = public_key_path.read_bytes()
        result = evaluate(
            contract,
            ledger,
            contract_path=contract_path,
            ledger_path=ledger_path,
            candidate_root=Path(args.candidate_root).resolve(),
            verifier_path=verifier_path,
            public_key_path=public_key_path,
            contract_bytes=contract_bytes,
            ledger_bytes=ledger_bytes,
            public_key_bytes=public_key_bytes,
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        result = {
            "ok": False,
            "closed": False,
            "decision": "invalid",
            "errors": [str(exc)],
        }

    if args.expected_verifier_sha256:
        actual = (result.get("trust") or {}).get("verifier_sha256")
        if actual != args.expected_verifier_sha256:
            result.setdefault("errors", []).append(
                "executing verifier does not match host-expected SHA-256"
            )
            result["ok"] = False
            result["closed"] = False
            result["decision"] = "invalid"

    if args.json or not result.get("ok"):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"iteration convergence decision: {result['decision']}")
    if not result.get("ok"):
        return 2
    if args.require_close and result.get("decision") != "close":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
