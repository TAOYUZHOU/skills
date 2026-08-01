from __future__ import annotations

import copy
import hashlib
import hmac
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


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
CAPTURE_SCRIPT = SCRIPT.with_name("capture_harp_history_replay.py")
CAPTURE_SPEC = importlib.util.spec_from_file_location("harp_history_capture", CAPTURE_SCRIPT)
assert CAPTURE_SPEC and CAPTURE_SPEC.loader
capture = importlib.util.module_from_spec(CAPTURE_SPEC)
CAPTURE_SPEC.loader.exec_module(capture)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_receipt(manifest: Path) -> dict:
    return {
        "schema_version": 1,
        "status": "passed",
        "exit_code": 0,
        "command": "pytest -q tests/test_target_combined_lifecycle_chain.py",
        "candidate_revision": "1" * 40,
        "boundary_mode": "target_local_real_producers_consumers",
        "test_path": "tests/test_delivery_alignment_history_replay.py",
        "test_sha256": _sha256(Path(__file__)),
        "replay_manifest_sha256": _sha256(manifest),
        "stages": validator.CHAIN_STAGES,
        "stage_bindings": {
            stage: {
                "producer": f"target producer for {stage}",
                "consumer": f"target consumer for {stage}",
                "assertion": f"target postcondition for {stage}",
            }
            for stage in validator.CHAIN_STAGES
        },
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


def _sign(receipt: dict, key: Path) -> dict:
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    return receipt


def test_bundled_real_history_profiles_are_sanitized_and_reproducible() -> None:
    result = validator.validate_replay_manifest(
        FIXTURES / "manifest.json", require_host_attestation=False
    )
    assert result["ok"], result
    assert {row["archetype"] for row in result["profiles"]} == validator.ARCHETYPES
    assert all(row["oracle_ok"] for row in result["profiles"])


def test_combined_receipt_requires_all_ordered_stages_and_closure_oracles(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest = FIXTURES / "manifest.json"
    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(_sign(_valid_receipt(manifest), key), indent=2) + "\n",
        encoding="utf-8",
    )
    assert validator.validate_chain_receipt(receipt, manifest)["ok"]

    missing_stage = copy.deepcopy(_valid_receipt(manifest))
    missing_stage["stages"].remove("result_review_recorded")
    _sign(missing_stage, key)
    receipt.write_text(json.dumps(missing_stage), encoding="utf-8")
    result = validator.validate_chain_receipt(receipt, manifest)
    assert not result["ok"]
    assert "combined chain stages are missing, duplicated, or reordered" in result[
        "errors"
    ]


def test_combined_receipt_is_bound_to_the_exact_history_manifest(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest = FIXTURES / "manifest.json"
    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    receipt_data = _valid_receipt(manifest)
    receipt_data["replay_manifest_sha256"] = "0" * 64
    _sign(receipt_data, key)
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


def test_unsigned_self_authored_chain_receipt_is_rejected(tmp_path: Path) -> None:
    manifest = FIXTURES / "manifest.json"
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(_valid_receipt(manifest)), encoding="utf-8")
    result = validator.validate_chain_receipt(receipt, manifest)
    assert not result["ok"]
    assert "combined chain host attestation is invalid" in result["errors"]


def test_profile_extra_fields_cannot_smuggle_free_text(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, copied)
    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["profiles"][0]
    profile_path = copied / row["path"]
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["prompt"] = "secret-token-123"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    row["sha256"] = _sha256(profile_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validator.validate_replay_manifest(
        manifest_path, require_host_attestation=False
    )
    assert not result["ok"]
    assert any("profile keys mismatch" in error for error in result["errors"])


def test_selected_event_digest_is_recomputed(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, copied)
    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = next(
        value
        for value in manifest["profiles"]
        if value["archetype"] == "partial_result_materialization"
    )
    profile_path = copied / row["path"]
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["facts"]["review_events"][0]["event_seq"] += 1
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    row["sha256"] = _sha256(profile_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validator.validate_replay_manifest(
        manifest_path, require_host_attestation=False
    )
    assert not result["ok"]
    assert any("selected event provenance mismatch" in error for error in result["errors"])


def test_single_component_absolute_path_is_rejected(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, copied)
    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["profiles"][0]
    profile_path = copied / row["path"]
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["facts"]["completion"]["blockers"].append("/secret")
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    row["sha256"] = _sha256(profile_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validator.validate_replay_manifest(
        manifest_path, require_host_attestation=False
    )
    assert not result["ok"]
    assert any("absolute path leaked" in error for error in result["errors"])


def test_zero_size_source_provenance_is_rejected(tmp_path: Path) -> None:
    copied = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, copied)
    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest["profiles"]:
        profile_path = copied / row["path"]
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        for source in profile["source_provenance"]["state_files"].values():
            source["sha256"] = "0" * 64
            source["size_bytes"] = 0
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        row["sha256"] = _sha256(profile_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validator.validate_replay_manifest(
        manifest_path, require_host_attestation=False
    )
    assert not result["ok"]
    assert any("provenance sizes are invalid" in error for error in result["errors"])


def test_capture_refuses_output_inside_a_historical_source(tmp_path: Path) -> None:
    sources = [tmp_path / f"source-{index}" for index in range(3)]
    for source in sources:
        source.mkdir()
    args = [sys.executable, str(CAPTURE_SCRIPT)]
    for label, archetype, source in zip(
        ("generic-review", "generic-blocked", "generic-partial"),
        sorted(capture.ARCHETYPES),
        sources,
    ):
        args.extend(["--source", f"{label}={archetype}:{source}"])
    output = sources[0] / "derived"
    args.extend(["--output-dir", str(output)])
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    assert result.returncode == 2
    assert "must not be a historical source" in result.stderr
    assert not output.exists()


def test_capture_rejects_a_torn_cross_file_snapshot(
    monkeypatch, tmp_path: Path,
) -> None:
    calls = 0

    def changing_snapshot(_state_dir: Path):
        nonlocal calls
        calls += 1
        return ({"epoch": calls}, {}, [])

    monkeypatch.setattr(capture, "_snapshot", changing_snapshot)
    with pytest.raises(RuntimeError, match="stable cross-file snapshot"):
        capture._capture("generic-review", "review_projection_mismatch", tmp_path)


def test_validation_results_do_not_persist_absolute_paths() -> None:
    result = validator.validate_replay_manifest(
        FIXTURES / "manifest.json", require_host_attestation=False
    )
    assert result["path"] == "manifest.json"
    assert "/" not in result["path"]
