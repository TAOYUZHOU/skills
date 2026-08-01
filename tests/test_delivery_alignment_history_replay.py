from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "delivery-alignment-iteration"
    / "scripts"
    / "validate_harp_chain_evidence.py"
)
FIXTURES = (
    ROOT
    / "skills"
    / "delivery-alignment-iteration"
    / "assets"
    / "harp-history-replays"
)
SPEC = importlib.util.spec_from_file_location("harp_chain_evidence", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_receipt(manifest: Path) -> dict:
    return {
        "schema_version": 1,
        "status": "passed",
        "exit_code": 0,
        "command": "pytest -q tests/test_target_combined_lifecycle_chain.py",
        "replay_manifest_sha256": _sha256(manifest),
        "stages": validator.CHAIN_STAGES,
        "replay_results": [
            {
                "archetype": archetype,
                "detected": True,
                "owner_routed": True,
                "review_required_when_applicable": True,
                "premature_completion_rejected": True,
                "later_health_audit_required": True,
            }
            for archetype in sorted(validator.ARCHETYPES)
        ],
        "happy_path": {
            "identity_preserved": True,
            "review_accepted": True,
            "artifact_gate_passed": True,
            "completion_true": True,
            "health_restored": True,
            "repeated_zero_work_wakeups": 0,
        },
    }


def test_bundled_real_history_profiles_are_sanitized_and_reproducible() -> None:
    result = validator.validate_replay_manifest(FIXTURES / "manifest.json")
    assert result["ok"], result
    assert {row["archetype"] for row in result["profiles"]} == validator.ARCHETYPES
    assert all(row["oracle_ok"] for row in result["profiles"])


def test_combined_receipt_requires_all_ordered_stages_and_closure_oracles(
    tmp_path: Path,
) -> None:
    manifest = FIXTURES / "manifest.json"
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(_valid_receipt(manifest), indent=2) + "\n", encoding="utf-8"
    )
    assert validator.validate_chain_receipt(receipt, manifest)["ok"]

    missing_stage = copy.deepcopy(_valid_receipt(manifest))
    missing_stage["stages"].remove("result_review_recorded")
    receipt.write_text(json.dumps(missing_stage), encoding="utf-8")
    result = validator.validate_chain_receipt(receipt, manifest)
    assert not result["ok"]
    assert "combined chain stages are missing, duplicated, or reordered" in result[
        "errors"
    ]


def test_combined_receipt_is_bound_to_the_exact_history_manifest(
    tmp_path: Path,
) -> None:
    manifest = FIXTURES / "manifest.json"
    receipt_data = _valid_receipt(manifest)
    receipt_data["replay_manifest_sha256"] = "0" * 64
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(receipt_data), encoding="utf-8")
    result = validator.validate_chain_receipt(receipt, manifest)
    assert not result["ok"]
    assert "combined chain is not bound to the replay manifest" in result["errors"]


def test_each_historical_profile_has_no_source_path_or_free_form_payload() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["profiles"]:
        raw = (FIXTURES / row["path"]).read_text(encoding="utf-8")
        profile = json.loads(raw)
        assert not validator.ABSOLUTE_PATH_RE.search(raw)
        assert profile["capture_mode"] == "read_only_whitelist"
        assert profile["authority"] == "historical_observation_only"
        assert set(profile["facts"]) == {
            "queue",
            "completion",
            "dag",
            "workflow_health",
            "review_events",
        }
