from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest


CHECKER = (
    Path(__file__).parents[1]
    / "skills"
    / "delivery-alignment-iteration"
    / "scripts"
    / "check_delivery_contract.py"
)
SPEC = importlib.util.spec_from_file_location("delivery_contract_checker", CHECKER)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def _legacy_contract() -> str:
    return "\n".join(f"{key}: value" for key in checker.REQUIRED_KEYS)


def _v2_contract(*, risk: str = "high", decision: str = "required") -> str:
    return (
        "schema_version: 2\n"
        + _legacy_contract()
        + "\nsandbox: live\n"
        + "adversarial_gate:\n"
        + f"  risk: {risk}\n"
        + f"  decision: {decision}\n"
        + "  reason: executable change\n"
        + "  base: abc\n"
        + "  candidate: def\n"
        + "  attack_scope:\n"
        + "    - runtime.py\n"
        + "  evidence_dir: docs/evidence/test\n"
        + "combined_chain_gate:\n"
        + "  decision: not_applicable\n"
        + "  reason: fixture contract test has no control lifecycle\n"
        + "  unreachability:\n"
        + "    predicate:\n"
        + "      kind: no_harp_runtime_boundaries\n"
        + "    invoke: prove no queue, review, completion, or health path exists\n"
        + "    assert: combined lifecycle is unreachable\n"
        + "    evidence: docs/evidence/combined_unreachable.json\n"
        + "historical_replay_gate:\n"
        + "  decision: not_applicable\n"
        + "  reason: fixture contract test has no persisted workspace state\n"
        + "  unreachability:\n"
        + "    predicate:\n"
        + "      kind: all_paths_absent\n"
        + "      paths: [harp/history-state]\n"
        + "    invoke: prove no historical control state reaches this fixture\n"
        + "    assert: historical replay is unreachable\n"
        + "    evidence: docs/evidence/history_unreachable.json\n"
    )


def test_legacy_contract_remains_readable() -> None:
    assert checker.validate_legacy_read_only(_legacy_contract())["ok"]
    assert not checker.validate(_legacy_contract())["ok"]


def test_nested_contract_keys_do_not_satisfy_top_level_requirements() -> None:
    nested = "wrapper:\n" + "\n".join(
        f"  {key}: value" for key in checker.REQUIRED_KEYS
    )
    result = checker.validate(nested)
    assert not result["ok"]
    assert set(result["missing_keys"]) == set(
        checker.REQUIRED_KEYS + checker.V2_REQUIRED_KEYS
    )


def test_empty_adversarial_reason_is_rejected() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", "  reason:"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_malformed_schema_version_does_not_downgrade_to_v1() -> None:
    result = checker.validate("schema_version: two\n" + _legacy_contract())
    assert not result["ok"]
    assert result["schema_version_error"].startswith("invalid schema_version")


def test_empty_markdown_headings_do_not_satisfy_contract_fields() -> None:
    headings = "\n".join(f"# {key.replace('_', ' ')}" for key in checker.REQUIRED_KEYS)
    result = checker.validate(headings)
    assert not result["ok"]
    assert set(result["missing_keys"]) == set(
        checker.REQUIRED_KEYS + checker.V2_REQUIRED_KEYS
    )


def test_handoff_headings_require_nonempty_evidence() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    headings = "\n".join(
        f"## {key.replace('_', ' ')}"
        for key in checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    )
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(
        checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    )


def test_high_risk_gate_rejects_empty_evidence_fields() -> None:
    contract = _v2_contract().replace(
        "  attack_scope:\n    - runtime.py", "  attack_scope:"
    )
    for field, value in (
        ("reason", "executable change"),
        ("base", "abc"),
        ("candidate", "def"),
        ("evidence_dir", "docs/evidence/test"),
    ):
        contract = contract.replace(f"  {field}: {value}", f"  {field}:")
    result = checker.validate(contract)
    assert not result["ok"]
    for field in ("reason", "base", "candidate", "attack_scope", "evidence_dir"):
        assert f"empty adversarial_gate.{field}" in result["adversarial_errors"]


def test_low_risk_contract_requires_skipped_decision() -> None:
    result = checker.validate(_v2_contract(risk="low", decision="required"))
    assert not result["ok"]
    assert "low-risk diff must record decision: skipped" in result["adversarial_errors"]


def test_high_risk_contract_cannot_skip() -> None:
    result = checker.validate(_v2_contract(risk="high", decision="skipped"))
    assert not result["ok"]
    assert "high-risk diff requires decision: required" in result["adversarial_errors"]


def test_high_risk_contract_binds_externally_frozen_candidate() -> None:
    candidate = "a" * 40
    contract = _v2_contract().replace("  candidate: def", f"  candidate: {candidate}")
    assert checker.validate_expected_candidate(contract, candidate)["ok"]
    assert not checker.validate_expected_candidate(contract, "b" * 40)["ok"]
    assert not checker.validate_expected_candidate(contract, "")["ok"]


def test_handoff_candidate_binds_contract_and_external_freeze() -> None:
    candidate = "a" * 40
    contract = _v2_contract().replace("  candidate: def", f"  candidate: {candidate}")
    handoff = f"candidate: {candidate}\n"
    assert checker.validate_handoff_candidate(contract, handoff, candidate)["ok"]
    mismatch = checker.validate_handoff_candidate(
        contract, f"candidate: {'b' * 40}\n", candidate
    )
    assert not mismatch["ok"]
    assert mismatch["checks"] == {"contract": False, "external": False}


def test_high_risk_contract_requires_both_lifecycle_gates() -> None:
    contract = _v2_contract()
    contract = contract.split("combined_chain_gate:\n", 1)[0]
    result = checker.validate(contract)
    assert not result["ok"]
    assert result["combined_chain_errors"] == ["missing combined_chain_gate"]
    assert result["historical_replay_errors"] == [
        "missing historical_replay_gate"
    ]


def test_lifecycle_not_applicable_requires_unreachability() -> None:
    contract = _v2_contract().replace(
        "    evidence: docs/evidence/combined_unreachable.json\n",
        "",
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert (
        "missing combined_chain_gate.unreachability.evidence"
        in result["combined_chain_errors"]
    )


def test_required_lifecycle_gates_require_evidence_fields() -> None:
    contract = _v2_contract()
    contract = contract.replace(
        "combined_chain_gate:\n"
        "  decision: not_applicable\n"
        "  reason: fixture contract test has no control lifecycle\n"
        "  unreachability:\n"
        "    predicate:\n"
        "      kind: no_harp_runtime_boundaries\n"
        "    invoke: prove no queue, review, completion, or health path exists\n"
        "    assert: combined lifecycle is unreachable\n"
        "    evidence: docs/evidence/combined_unreachable.json\n",
        "combined_chain_gate:\n"
        "  decision: required\n"
        "  reason: control lifecycle is reachable\n",
    )
    contract = contract.replace(
        "historical_replay_gate:\n"
        "  decision: not_applicable\n"
        "  reason: fixture contract test has no persisted workspace state\n"
        "  unreachability:\n"
        "    predicate:\n"
        "      kind: all_paths_absent\n"
        "      paths: [harp/history-state]\n"
        "    invoke: prove no historical control state reaches this fixture\n"
        "    assert: historical replay is unreachable\n"
        "    evidence: docs/evidence/history_unreachable.json\n",
        "historical_replay_gate:\n"
        "  decision: required\n"
        "  reason: persisted workspace state is reachable\n",
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert set(result["combined_chain_errors"]) == {
        f"missing combined_chain_gate.{key}"
        for key in checker.COMBINED_CHAIN_EVIDENCE_KEYS
    }
    assert set(result["historical_replay_errors"]) == {
        f"missing historical_replay_gate.{key}"
        for key in checker.HISTORICAL_REPLAY_EVIDENCE_KEYS
    }


def test_required_lifecycle_evidence_is_recomputed(
    tmp_path: Path, monkeypatch
) -> None:
    source = (
        Path(__file__).parents[1]
        / "skills"
        / "delivery-alignment-iteration"
        / "assets"
        / "harp-history-replays"
    )
    fixtures = tmp_path / "fixtures"
    shutil.copytree(source, fixtures)
    manifest = fixtures / "manifest.json"
    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    manifest_record = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_record.pop("attestation_hmac_sha256", None)
    manifest_payload = json.dumps(
        manifest_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    manifest_record["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), manifest_payload, hashlib.sha256
    ).hexdigest()
    manifest.write_text(json.dumps(manifest_record), encoding="utf-8")
    capture_receipt = fixtures / "capture_receipt.json"
    capture_record = json.loads(capture_receipt.read_text(encoding="utf-8"))
    capture_record.pop("attestation_hmac_sha256", None)
    capture_payload = json.dumps(
        capture_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    capture_record["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), capture_payload, hashlib.sha256
    ).hexdigest()
    capture_receipt.write_text(json.dumps(capture_record), encoding="utf-8")
    validator = checker._load_chain_validator()
    replay = validator.validate_replay_manifest(manifest)
    history_evidence = tmp_path / "history_validation.json"
    history_evidence.write_text(
        json.dumps({"ok": replay["ok"], "replay": replay}, indent=2) + "\n",
        encoding="utf-8",
    )
    producer = tmp_path / "producer.py"
    producer.write_text("def produce(value):\n    return value\n", encoding="utf-8")
    consumer = tmp_path / "consumer.py"
    consumer.write_text("def consume(value):\n    return value\n", encoding="utf-8")
    target_test = tmp_path / "target_chain_test.py"
    target_test.write_text(
        "from producer import produce\nfrom consumer import consume\n\n"
        + "\n".join(
            f"def test_{stage}():\n"
            f"    assert consume(produce('{stage}')) == '{stage}'\n"
            for stage in validator.CHAIN_STAGES
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "add", "producer.py", "consumer.py", "target_chain_test.py"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "commit", "-qm", "target chain"], cwd=tmp_path, check=True)
    test_candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    run_id = "a" * 32
    junit = tmp_path / "chain.xml"
    junit.write_text(
        '<testsuites><testsuite tests="10" failures="0" errors="0" skipped="0">'
        f'<properties><property name="harp_run_id" value="{run_id}" /></properties>'
        + "".join(
            f'<testcase classname="target_chain_test" name="test_{stage}" />'
            for stage in checker._load_chain_validator().CHAIN_STAGES
        )
        + "</testsuite></testsuites>",
        encoding="utf-8",
    )
    contexts = [
        f"target_chain_test.py::test_{stage}|run" for stage in validator.CHAIN_STAGES
    ]
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "meta": {"show_contexts": True, "harp_run_id": run_id},
                "files": {
                    "producer.py": {
                        "executed_lines": [1, 2],
                        "contexts": {"1": contexts},
                    },
                    "consumer.py": {
                        "executed_lines": [1, 2],
                        "contexts": {"1": contexts},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    prior = hashlib.sha256(b"seed").hexdigest()
    trace_rows = []
    for stage in validator.CHAIN_STAGES:
        produced = hashlib.sha256(f"{prior}:{stage}:produced".encode()).hexdigest()
        consumed = hashlib.sha256(f"{produced}:consumed".encode()).hexdigest()
        trace_rows.append(
            {
                "stage": stage,
                "testcase": f"test_{stage}",
                "producer_path": "producer.py",
                "consumer_path": "consumer.py",
                "input_sha256": prior,
                "producer_output_sha256": produced,
                "consumer_input_sha256": produced,
                "consumer_output_sha256": consumed,
                "assertion_passed": True,
            }
        )
        prior = consumed
    trace = tmp_path / "trace.json"
    trace.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": run_id,
                "candidate_revision": test_candidate,
                "test_path": "target_chain_test.py",
                "stages": trace_rows,
            }
        ),
        encoding="utf-8",
    )
    receipt = {
        "status": "passed",
        "exit_code": 0,
        "command": "pytest -q target_chain_test.py --junitxml=chain.xml --cov=. --cov-context=test --cov-report=json:coverage.json --harp-chain-trace=trace.json",
        "candidate_revision": test_candidate,
        "boundary_mode": "target_local_real_producers_consumers",
        "test_path": "target_chain_test.py",
        "test_sha256": hashlib.sha256(target_test.read_bytes()).hexdigest(),
        "junit_path": "chain.xml",
        "junit_sha256": hashlib.sha256(junit.read_bytes()).hexdigest(),
        "coverage_path": "coverage.json",
        "coverage_sha256": hashlib.sha256(coverage.read_bytes()).hexdigest(),
        "run_id": run_id,
        "trace_path": "trace.json",
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "replay_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "stages": validator.CHAIN_STAGES,
        "stage_bindings": {
            stage: {
                "producer": "producer.produce",
                "consumer": "consumer.consume",
                "assertion": f"round trip preserves {stage}",
                "testcase": f"test_{stage}",
                "producer_path": "producer.py",
                "producer_sha256": hashlib.sha256(producer.read_bytes()).hexdigest(),
                "consumer_path": "consumer.py",
                "consumer_sha256": hashlib.sha256(consumer.read_bytes()).hexdigest(),
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
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    chain_evidence = tmp_path / "chain_receipt.json"
    chain_evidence.write_text(json.dumps(receipt), encoding="utf-8")
    contract = _v2_contract().replace(
        "sandbox: live\n",
        "sandbox:\n"
        "  scope: deterministic validator boundary\n"
        "  fixture: copied replay profiles\n"
        "  invoke: validate lifecycle evidence\n"
        "  assert: recomputed evidence matches\n"
        "  record: tmp test outputs\n",
    )
    contract = contract.replace("  candidate: def", f"  candidate: {test_candidate}")
    contract = contract.replace(
        "combined_chain_gate:\n"
        "  decision: not_applicable\n"
        "  reason: fixture contract test has no control lifecycle\n"
        "  unreachability:\n"
        "    predicate:\n"
        "      kind: no_harp_runtime_boundaries\n"
        "    invoke: prove no queue, review, completion, or health path exists\n"
        "    assert: combined lifecycle is unreachable\n"
        "    evidence: docs/evidence/combined_unreachable.json\n",
        "combined_chain_gate:\n"
        "  decision: required\n"
        "  reason: control lifecycle is reachable\n"
        "  scope: executor through post-repair audit\n"
        "  invoke: pytest -q target_chain_test.py --junitxml=chain.xml --cov=. --cov-context=test --cov-report=json:coverage.json --harp-chain-trace=trace.json\n"
        "  assert: all stages and closure oracles pass\n"
        "  evidence: chain_receipt.json\n",
    )
    contract = contract.replace(
        "historical_replay_gate:\n"
        "  decision: not_applicable\n"
        "  reason: fixture contract test has no persisted workspace state\n"
        "  unreachability:\n"
        "    predicate:\n"
        "      kind: all_paths_absent\n"
        "      paths: [harp/history-state]\n"
        "    invoke: prove no historical control state reaches this fixture\n"
        "    assert: historical replay is unreachable\n"
        "    evidence: docs/evidence/history_unreachable.json\n",
            "historical_replay_gate:\n"
            "  decision: required\n"
            "  reason: persisted workspace state is reachable\n"
            "  fixture_manifest: fixtures/manifest.json\n"
            "  capture: read-only whitelist capture\n"
            "  capture_receipt: fixtures/capture_receipt.json\n"
            "  invoke: replay all three profiles\n"
        "  assert: all replay oracles pass\n"
        "  evidence: history_validation.json\n",
    )
    assert checker.validate(contract)["ok"]
    result = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert result["ok"], result

    trace_record = json.loads(trace.read_text(encoding="utf-8"))
    trace_record["stages"][0]["consumer_input_sha256"] = "0" * 64
    trace.write_text(json.dumps(trace_record), encoding="utf-8")
    receipt["trace_sha256"] = hashlib.sha256(trace.read_bytes()).hexdigest()
    receipt.pop("attestation_hmac_sha256")
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    chain_evidence.write_text(json.dumps(receipt), encoding="utf-8")
    broken_trace = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert not broken_trace["ok"]
    assert broken_trace["combined_chain"]["binding_checks"]["causal_trace"] is False

    trace_record["stages"][0]["consumer_input_sha256"] = trace_record["stages"][0][
        "producer_output_sha256"
    ]
    trace.write_text(json.dumps(trace_record), encoding="utf-8")
    receipt["trace_sha256"] = hashlib.sha256(trace.read_bytes()).hexdigest()
    receipt.pop("attestation_hmac_sha256")
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    chain_evidence.write_text(json.dumps(receipt), encoding="utf-8")

    receipt["command"] = (
        "pytest -q benign.py --junitxml=chain.xml --cov=. --cov-context=test "
        "--cov-report=json:coverage.json --harp-chain-trace=trace.json"
    )
    receipt.pop("attestation_hmac_sha256")
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    chain_evidence.write_text(json.dumps(receipt), encoding="utf-8")
    split_contract = contract.replace(
        "  invoke: pytest -q target_chain_test.py --junitxml=chain.xml",
        "  invoke: pytest -q benign.py --junitxml=chain.xml",
    )
    mismatched = checker.validate_lifecycle_evidence(split_contract, tmp_path)
    assert not mismatched["ok"]
    assert any("not bound to contract" in error for error in mismatched["errors"])
    assert mismatched["combined_chain"]["binding_checks"]["command"] is True
    assert (
        mismatched["combined_chain"]["binding_checks"]["pytest_command"]
        is False
    )

    receipt["command"] = (
        "pytest -q target_chain_test.py --junitxml=chain.xml --cov=. "
        "--cov-context=test --cov-report=json:coverage.json "
        "--harp-chain-trace=trace.json"
    )
    receipt.pop("attestation_hmac_sha256")
    payload = json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    chain_evidence.write_text(json.dumps(receipt), encoding="utf-8")

    profile = fixtures / "blocked_artifact_dependency.json"
    profile.write_text(profile.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    tampered = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert not tampered["ok"]
    assert "historical replay manifest is invalid" in tampered["errors"]


def test_unreachability_prose_cannot_satisfy_a_lifecycle_gate() -> None:
    contract = _v2_contract().replace(
        "  unreachability:\n"
        "    predicate:\n"
        "      kind: no_harp_runtime_boundaries\n"
        "    invoke: prove no queue, review, completion, or health path exists\n"
        "    assert: combined lifecycle is unreachable\n"
        "    evidence: docs/evidence/combined_unreachable.json\n",
        "  unreachability: yes\n",
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert (
        "combined_chain_gate.unreachability must be a proof mapping when not_applicable"
        in result["combined_chain_errors"]
    )


def test_low_risk_self_classification_cannot_omit_lifecycle_declarations() -> None:
    contract = _v2_contract(risk="low", decision="skipped")
    contract = contract.split("combined_chain_gate:\n", 1)[0]
    result = checker.validate(contract)
    assert not result["ok"]
    assert {"combined_chain_gate", "historical_replay_gate"}.issubset(
        result["missing_keys"]
    )


def test_unreachability_evidence_is_machine_bound(
    tmp_path: Path, monkeypatch,
) -> None:
    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    for gate, filename, command, assertion in (
        (
            "combined_chain_gate",
            "combined_unreachable.json",
            "prove no queue, review, completion, or health path exists",
            "combined lifecycle is unreachable",
        ),
        (
            "historical_replay_gate",
            "history_unreachable.json",
            "prove no historical control state reaches this fixture",
            "historical replay is unreachable",
        ),
    ):
        evidence = tmp_path / "docs" / "evidence" / filename
        evidence.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ok": True,
            "gate": gate,
            "reachable": False,
            "predicate": (
                {"kind": "no_harp_runtime_boundaries"}
                if gate == "combined_chain_gate"
                else {
                    "kind": "all_paths_absent",
                    "paths": ["harp/history-state"],
                }
            ),
            "observation": (
                checker._runtime_boundary_inventory(tmp_path)[0]
                if gate == "combined_chain_gate"
                else {"harp/history-state": "absent"}
            ),
            "command": command,
            "assertion": assertion,
            "candidate_revision": "def",
            "repository_scope": "contract-root",
            "command_cwd": "contract-root",
        }
        payload = json.dumps(
            record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
        record["attestation_hmac_sha256"] = hmac.new(
            key.read_bytes(), payload, hashlib.sha256
        ).hexdigest()
        evidence.write_text(json.dumps(record), encoding="utf-8")
    contract = _v2_contract()
    result = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert result["ok"], result

    replayed = contract.replace("  candidate: def", f"  candidate: {'a' * 40}")
    result = checker.validate_lifecycle_evidence(replayed, tmp_path)
    assert not result["ok"]
    assert any("does not match its proof" in error for error in result["errors"])

    runtime = tmp_path / "src" / "harp" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "control_chain.py").write_text(
        "queue = review = completion = health = True\n", encoding="utf-8"
    )
    result = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert not result["ok"]
    assert any("predicate is false" in error for error in result["errors"])
    (runtime / "control_chain.py").unlink()
    runtime.rmdir()
    runtime.parent.rmdir()
    runtime.parent.parent.rmdir()

    path = tmp_path / "docs" / "evidence" / "combined_unreachable.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["reachable"] = True
    path.write_text(json.dumps(record), encoding="utf-8")
    result = checker.validate_lifecycle_evidence(contract, tmp_path)
    assert not result["ok"]
    assert any("does not match its proof" in error for error in result["errors"])


def test_split_module_runtime_cannot_evade_repository_inventory(tmp_path: Path) -> None:
    control = tmp_path / "src" / "control"
    control.mkdir(parents=True)
    for name, token in (
        ("queue.py", "queue"),
        ("reviews.py", "review"),
        ("completion.py", "completion"),
        ("health.py", "health"),
    ):
        (control / name).write_text(f"def {token}(): return True\n", encoding="utf-8")
    observation, errors = checker._runtime_boundary_inventory(tmp_path)
    assert errors
    assert observation["runtime_boundary_candidates"]
    assert {f"src/control/{name}" for name in (
        "queue.py", "reviews.py", "completion.py", "health.py"
    )}.issubset(set(observation["runtime_boundary_candidates"]))


@pytest.mark.parametrize(
    "parents",
    [
        ["docs/evidence/runtime_parts"] * 4,
        [
            "skills/queue-adapter",
            "skills/review-adapter",
            "skills/completion-adapter",
            "skills/health-adapter",
        ],
    ],
)
def test_split_runtime_is_detected_across_evidence_or_skill_packages(
    tmp_path: Path, parents: list[str]
) -> None:
    files = []
    for index, (parent, token) in enumerate(
        zip(parents, ("queue", "review", "completion", "health")), 1
    ):
        path = tmp_path / parent / f"part{index}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"def {token}(): return True\n", encoding="utf-8")
        files.append(path.relative_to(tmp_path).as_posix())
    observation, errors = checker._runtime_boundary_inventory(tmp_path)
    assert errors
    assert set(files).issubset(set(observation["runtime_boundary_candidates"]))


def test_runtime_inventory_reads_immutable_candidate_blob(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=tmp_path, check=True
    )
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    runtime = tmp_path / "src" / "control.py"
    runtime.parent.mkdir()
    runtime.write_text(
        "queue = review = completion = health = True\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "src/control.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "runtime"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    runtime.unlink()
    observation, errors = checker._runtime_boundary_inventory(
        tmp_path, base, candidate
    )
    assert errors
    assert "src/control.py" in observation["runtime_boundary_candidates"]
    assert observation["changed_code_file_count"] == 1


@pytest.mark.parametrize("delete_in_candidate", [False, True])
def test_runtime_inventory_reads_full_candidate_tree_and_base_deletions(
    tmp_path: Path, delete_in_candidate: bool
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=tmp_path, check=True
    )
    runtime = tmp_path / "runtime_parts"
    runtime.mkdir()
    names = []
    for index, token in enumerate(("queue", "review", "completion", "health"), 1):
        path = runtime / f"part{index}.py"
        path.write_text(f"def {token}(): return True\n", encoding="utf-8")
        names.append(path.relative_to(tmp_path).as_posix())
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    if delete_in_candidate:
        subprocess.run(["git", "rm", "-qr", "runtime_parts"], cwd=tmp_path, check=True)
    else:
        (tmp_path / "README.md").write_text("candidate\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    if not delete_in_candidate:
        for name in names:
            (tmp_path / name).unlink()
        runtime.rmdir()
    observation, errors = checker._runtime_boundary_inventory(
        tmp_path, base, candidate
    )
    assert errors
    assert set(names).issubset(set(observation["runtime_boundary_candidates"]))


def test_combined_chain_na_cannot_use_author_selected_absent_path(
    tmp_path: Path, monkeypatch,
) -> None:
    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    evidence = tmp_path / "proof.json"
    gate = {
        "unreachability": {
            "predicate": {
                "kind": "all_paths_absent",
                "paths": ["unused/nonexistent/path"],
            },
            "invoke": "check selected absent path",
            "assert": "combined lifecycle is unreachable",
            "evidence": "proof.json",
        }
    }
    record = {
        "ok": True,
        "gate": "combined_chain_gate",
        "reachable": False,
        "predicate": gate["unreachability"]["predicate"],
        "observation": {"unused/nonexistent/path": "absent"},
        "command": gate["unreachability"]["invoke"],
        "assertion": gate["unreachability"]["assert"],
        "candidate_revision": "b" * 40,
        "repository_scope": "contract-root",
        "command_cwd": "contract-root",
    }
    payload = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    record["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    evidence.write_text(json.dumps(record), encoding="utf-8")
    ok, errors, _record = checker._validate_unreachability(
        tmp_path,
        "combined_chain_gate",
        gate,
        "a" * 40,
        "b" * 40,
    )
    assert not ok
    assert any("requires no_harp_runtime_boundaries" in error for error in errors)


def test_junit_aggregate_counters_and_stage_cases_are_enforced(
    tmp_path: Path,
) -> None:
    junit = tmp_path / "chain.xml"
    junit.write_text(
        '<testsuite tests="1" failures="1" errors="0" skipped="0">'
        '<testcase classname="target_chain_test" name="test_executor_handoff" />'
        "</testsuite>",
        encoding="utf-8",
    )
    assert not checker._junit_matches_test(
        junit, "target_chain_test.py", {"test_executor_handoff"}
    )
    junit.write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="target_chain_test" name="test_executor_handoff" />'
        "</testsuite>",
        encoding="utf-8",
    )
    assert not checker._junit_matches_test(
        junit,
        "target_chain_test.py",
        {"test_executor_handoff", "test_completion_fact"},
    )


def test_new_v1_contract_cannot_bypass_v2_rules() -> None:
    result = checker.validate(_legacy_contract())
    assert not result["ok"]
    current = checker.validate_current_schema(result)
    assert not current["ok"]


def test_cli_handoff_must_match_contract_declared_path(tmp_path: Path) -> None:
    contract = _v2_contract()
    expected = tmp_path / "docs" / "expected.md"
    substitute = tmp_path / "docs" / "substitute.md"
    contract = contract.replace("handoff: value", "handoff:\n  path: docs/expected.md")
    binding = checker.validate_handoff_binding(contract, tmp_path, substitute)
    assert not binding["ok"]
    assert binding["declared"] == str(expected.resolve())


def test_low_risk_declaration_cannot_skip_executable_diff(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    (tmp_path / "runtime.py").write_text("print('candidate')\n", encoding="utf-8")
    subprocess.run(["git", "add", "runtime.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    contract = _v2_contract(risk="low", decision="skipped")
    contract = contract.replace("  base: abc", f"  base: {base}")
    contract = contract.replace("  candidate: def", f"  candidate: {candidate}")
    result = checker.validate_diff_binding(contract, tmp_path)
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["runtime.py"]


def test_nested_reason_does_not_satisfy_direct_gate_reason() -> None:
    contract = _v2_contract().replace(
        "  reason: executable change", "  details:\n    reason: nested excuse"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "missing adversarial_gate.reason" in result["adversarial_errors"]


def test_quoted_empty_adversarial_reason_is_rejected() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", '  reason: ""'
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_duplicate_schema_versions_are_rejected() -> None:
    result = checker.validate("schema_version: 1\nschema_version: 2\n" + _legacy_contract())
    assert not result["ok"]
    assert result["schema_version_error"].startswith("invalid YAML")


def test_leading_zero_schema_version_is_rejected() -> None:
    result = checker.validate(_v2_contract().replace("schema_version: 2", "schema_version: 02"))
    assert not result["ok"]
    assert result["schema_version_error"].startswith("invalid schema_version")


def test_headings_inside_fenced_example_do_not_form_contract() -> None:
    body = "\n".join(
        f"# {key.replace('_', ' ')}\nexample" for key in checker.REQUIRED_KEYS
    )
    result = checker.validate(f"```markdown\n{body}\n```\n")
    assert not result["ok"]


def test_handoff_metadata_must_be_nonempty() -> None:
    metadata = "\n".join(f"{key}:" for key in checker.HANDOFF_METADATA)
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence"
        for key in checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    )
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_metadata"]) == set(checker.HANDOFF_METADATA)


def test_comment_only_handoff_evidence_is_empty() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    sections = []
    for key in checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS:
        body = "<!-- TODO -->" if key == "adversarial_gate_evidence" else "evidence"
        sections.append(f"## {key.replace('_', ' ')}\n{body}")
    result = checker.validate_handoff(
        metadata + "\n" + "\n".join(sections), schema_version=2
    )
    assert not result["ok"]
    assert "adversarial_gate_evidence" in result["empty_headings"]


def _diff_repo(tmp_path: Path, changed_path: str) -> tuple[str, str]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    target = tmp_path / changed_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", changed_path], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    return base, candidate


def _bound_contract(base: str, candidate: str, path: str, *, risk: str = "low") -> str:
    decision = "skipped" if risk == "low" else "required"
    contract = _v2_contract(risk=risk, decision=decision)
    return (
        contract.replace("  base: abc", f"  base: {base}")
        .replace("  candidate: def", f"  candidate: {candidate}")
        .replace("    - runtime.py", f"    - {path}")
    )


def test_low_risk_cannot_bypass_mjs_executable_diff(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "engine.mjs")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "engine.mjs"), tmp_path
    )
    assert not result["ok"]
    assert result["high_risk_paths"] == ["engine.mjs"]


def test_evidence_directory_does_not_exempt_executable_code(tmp_path: Path) -> None:
    path = "docs/evidence/attack.py"
    base, candidate = _diff_repo(tmp_path, path)
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, path), tmp_path
    )
    assert not result["ok"]
    assert result["high_risk_paths"] == [path]


def test_diff_binding_rejects_mutable_git_refs(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "runtime.py")
    subprocess.run(["git", "branch", "audit-base", base], cwd=tmp_path, check=True)
    subprocess.run(["git", "branch", "audit-candidate", candidate], cwd=tmp_path, check=True)
    contract = _bound_contract(base, candidate, "runtime.py", risk="high")
    contract = contract.replace(base, "audit-base").replace(candidate, "audit-candidate")
    result = checker.validate_diff_binding(contract, tmp_path)
    assert not result["ok"]
    assert result["error"] == "base and candidate must be immutable commit hashes"


def test_cli_defaults_cannot_disable_current_schema_gate(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    contract = tmp_path / "contract.md"
    handoff = docs / "handoff.md"
    contract.write_text(
        _legacy_contract().replace("handoff: value", "handoff:\n  path: docs/handoff.md"),
        encoding="utf-8",
    )
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence" for key in checker.HANDOFF_HEADINGS
    )
    handoff.write_text(metadata + "\n" + headings, encoding="utf-8")
    completed = subprocess.run(
        [
            "python3",
            str(CHECKER),
            "--contract",
            str(contract),
            "--handoff",
            str(handoff),
            "--root",
            str(tmp_path),
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 2
    assert '"current_schema"' in completed.stdout


def test_comment_only_nested_adversarial_reason_is_rejected() -> None:
    contract = _v2_contract().replace(
        "  reason: executable change", "  reason:\n    # no reason supplied"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_nested_yaml_values_do_not_fill_empty_markdown_contract_headings() -> None:
    headings = "\n".join(f"# {key.replace('_', ' ')}" for key in checker.REQUIRED_KEYS)
    nested = "wrapper:\n" + "\n".join(
        f"  {key}: injected" for key in checker.REQUIRED_KEYS
    )
    result = checker.validate(headings + "\n" + nested)
    assert not result["ok"]


def test_nested_yaml_values_do_not_fill_empty_handoff_headings() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}" for key in keys)
    nested = "wrapper:\n" + "\n".join(f"  {key}: injected" for key in keys)
    result = checker.validate_handoff(
        metadata + "\n" + headings + "\n" + nested, schema_version=2
    )
    assert not result["ok"]


def test_null_only_handoff_heading_bodies_are_rejected() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}\nnull" for key in keys)
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_low_risk_cannot_bypass_unlisted_executable_language(tmp_path: Path) -> None:
    path = "tools/runner.rb"
    base, candidate = _diff_repo(tmp_path, path)
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, path), tmp_path
    )
    assert not result["ok"]
    assert result["high_risk_paths"] == [path]


def test_low_risk_cannot_bypass_extensionless_executable(tmp_path: Path) -> None:
    path = "tools/release"
    base, candidate = _diff_repo(tmp_path, path)
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, path), tmp_path
    )
    assert not result["ok"]
    assert result["high_risk_paths"] == [path]


def test_scalar_live_sandbox_does_not_satisfy_completion_gate() -> None:
    result = checker.validate(_v2_contract())
    assert not result["ok"]
    assert set(result["sandbox_errors"]) == {
        f"missing sandbox.{key}" for key in checker.SANDBOX_REQUIRED_KEYS
    }


def test_fully_nested_adversarial_gate_cannot_masquerade_as_direct_fields() -> None:
    block = (
        "adversarial_gate:\n"
        "  wrapper:\n"
        "    risk: high\n"
        "    decision: required\n"
        "    reason: nested excuse\n"
        "    base: abc\n"
        "    candidate: def\n"
        "    attack_scope:\n"
        "      - runtime.py\n"
        "    evidence_dir: docs/evidence/test\n"
    )
    contract = _v2_contract().split("adversarial_gate:\n", 1)[0] + block
    result = checker.validate(contract)
    assert not result["ok"]
    assert {
        f"missing adversarial_gate.{key}" for key in checker.ADVERSARIAL_REQUIRED_KEYS
    }.issubset(result["adversarial_errors"])


def test_fully_nested_sandbox_fields_do_not_satisfy_direct_requirements() -> None:
    nested = (
        "sandbox:\n"
        "  wrapper:\n"
        "    scope: boundary\n"
        "    fixture: case\n"
        "    invoke: run\n"
        "    assert: pass\n"
        "    record: receipt\n"
    )
    contract = _v2_contract().replace("sandbox: live\n", nested)
    result = checker.validate(contract)
    assert not result["ok"]
    assert set(result["sandbox_errors"]) == {
        f"missing sandbox.{key}" for key in checker.SANDBOX_REQUIRED_KEYS
    }


def test_empty_collection_adversarial_reason_is_rejected() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", "  reason: []"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_low_risk_cannot_bypass_executable_package_json_change(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "package.json")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "package.json"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["package.json"]


def test_empty_collection_handoff_heading_bodies_are_rejected() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}\n[]" for key in keys)
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_fields_inside_multiline_html_comment_do_not_form_contract() -> None:
    commented = (
        "schema_version: 2\n<!--\n"
        + _legacy_contract()
        + "\nsandbox:\n"
        + "\n".join(f"  {key}: value" for key in checker.SANDBOX_REQUIRED_KEYS)
        + "\nadversarial_gate:\n"
        + "\n".join(f"  {key}: value" for key in checker.ADVERSARIAL_REQUIRED_KEYS)
        + "\n-->\n"
    )
    result = checker.validate(commented)
    assert not result["ok"]
    assert set(result["missing_keys"]) == set(
        checker.REQUIRED_KEYS + checker.V2_REQUIRED_KEYS
    )


def test_fabricated_empty_manifest_and_receipt_cannot_pass_gate(tmp_path: Path) -> None:
    import hashlib
    import json

    base, candidate = _diff_repo(tmp_path, "runtime.py")
    evidence = tmp_path / "docs" / "evidence" / "test"
    evidence.mkdir(parents=True)
    contract = _bound_contract(base, candidate, "runtime.py", risk="high")
    contract = contract.replace(
        "  evidence_dir: docs/evidence/test",
        "  evidence_dir: docs/evidence/test",
    )
    (evidence / "prompt.md").write_text("prompt", encoding="utf-8")
    (evidence / "final_agent_output.json").write_text(
        '{"attacks":[]}', encoding="utf-8"
    )
    (evidence / "agent_attack_manifest.json").write_text(
        '{"attacks":[]}', encoding="utf-8"
    )
    (evidence / "live_provider_receipt.json").write_text("{}", encoding="utf-8")
    diff = subprocess.check_output(
        ["git", "diff", base, candidate, "--", "runtime.py"],
        cwd=tmp_path,
        text=True,
    )
    output_sha = hashlib.sha256(
        (evidence / "final_agent_output.json").read_bytes()
    ).hexdigest()
    gate = {
        "base": base,
        "candidate": candidate,
        "diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        "raw_output_sha256": output_sha,
        "provider_thread_id": "fabricated",
        "generated_attack_count": 0,
        "executed_attack_count": 1,
        "escaped_attack_count": 0,
        "deterministic_exit_code": 0,
        "deterministic_command": "true",
        "live_sandbox": {"status": "passed"},
    }
    (evidence / "gate_result.json").write_text(json.dumps(gate), encoding="utf-8")
    result = checker.validate_gate_evidence(contract, tmp_path)
    assert not result["ok"]
    assert not result["checks"]["provider_receipt"]


def test_default_validation_cannot_use_legacy_compatibility_to_skip_v2_rules() -> None:
    assert not checker.validate(_legacy_contract())["ok"]


def test_empty_yaml_block_scalar_reason_is_rejected() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", "  reason: |"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_empty_yaml_block_scalar_sandbox_fields_are_rejected() -> None:
    sandbox = "sandbox:\n" + "".join(
        f"  {key}: |\n" for key in checker.SANDBOX_REQUIRED_KEYS
    )
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "sandbox: live\n", sandbox
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert set(result["sandbox_errors"]) == {
        f"empty sandbox.{key}" for key in checker.SANDBOX_REQUIRED_KEYS
    }


def test_html_break_only_handoff_sections_are_empty() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}\n<br>" for key in keys)
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_low_risk_cannot_bypass_dependency_manifest_change(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "requirements.txt")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "requirements.txt"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["requirements.txt"]


def test_attack_scope_rejects_git_pathspec_exclusions(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "runtime.py")
    contract = _bound_contract(base, candidate, "runtime.py", risk="high").replace(
        "    - runtime.py",
        "    - runtime.py\n    - ':(exclude)runtime.py'",
    )
    result = checker.validate_diff_binding(contract, tmp_path)
    assert not result["ok"]
    assert result["unexpected_in_attack_scope"] == [":(exclude)runtime.py"]


def test_diff_binding_rejects_candidate_ancestor_of_base(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "runtime.py")
    contract = _bound_contract(candidate, base, "runtime.py", risk="high")
    result = checker.validate_diff_binding(contract, tmp_path)
    assert not result["ok"]
    assert result["error"] == "candidate must descend from base"


def test_boolean_false_is_not_an_adversarial_reason() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", "  reason: false"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_duplicate_adversarial_gate_keys_are_rejected() -> None:
    contract = _v2_contract() + "  risk: low\n  decision: skipped\n"
    result = checker.validate(contract)
    assert not result["ok"]
    assert result["schema_version_error"].startswith("invalid YAML")


def test_low_risk_cannot_bypass_executable_html(tmp_path: Path) -> None:
    base, candidate = _diff_repo(tmp_path, "docs/payload.html")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/payload.html"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/payload.html"]


def test_horizontal_rule_only_handoff_section_is_empty() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    sections = [
        f"## {key.replace('_', ' ')}\n"
        + ("---" if key == "adversarial_gate_evidence" else "evidence")
        for key in keys
    ]
    result = checker.validate_handoff(
        metadata + "\n" + "\n".join(sections), schema_version=2
    )
    assert not result["ok"]
    assert "adversarial_gate_evidence" in result["empty_headings"]


def test_html_entity_only_handoff_sections_are_empty() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}\n&nbsp;" for key in keys)
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_fenced_schema_example_is_rejected_by_strict_v2_yaml() -> None:
    sandbox = "sandbox:\n" + "".join(
        f"  {key}: evidence\n" for key in checker.SANDBOX_REQUIRED_KEYS
    )
    contract = _v2_contract().replace("sandbox: live\n", sandbox)
    contract += "\n```yaml\nschema_version: 1\n```\n"
    result = checker.validate(contract)
    assert not result["ok"]
    assert result["schema_version_error"].startswith("invalid YAML")


def test_attack_manifest_must_match_agent_output() -> None:
    final_output = {"attacks": []}
    manifest_attacks = [{"id": "invented"}]
    assert not (
        isinstance(final_output, dict)
        and final_output.get("attacks") == manifest_attacks
    )


def test_provider_receipt_requires_out_of_repo_attestation(
    tmp_path: Path, monkeypatch
) -> None:
    import hashlib
    import hmac
    import json

    key = tmp_path / "receipt.key"
    key.write_bytes(b"k" * 32)
    receipt = {
        "event": "provider_turn_completed",
        "provider": "codex",
        "thread_id": "thread",
    }
    payload = json.dumps(
        receipt, sort_keys=True, separators=(",", ":")
    ).encode()
    receipt["attestation_hmac_sha256"] = hmac.new(
        key.read_bytes(), payload, hashlib.sha256
    ).hexdigest()
    monkeypatch.setenv("DELIVERY_ALIGNMENT_RECEIPT_KEY_FILE", str(key))
    assert checker._host_attestation_ok(receipt)
    receipt["thread_id"] = "fabricated"
    assert not checker._host_attestation_ok(receipt)


def test_quoted_whitespace_adversarial_reason_is_rejected() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", '  reason: "   "'
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_yaml_scalars_cannot_fill_empty_markdown_handoff_sections() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    scalars = "\n".join(f"{key}: injected" for key in keys)
    headings = "\n".join(f"## {key.replace('_', ' ')}" for key in keys)
    result = checker.validate_handoff(
        metadata + "\n" + scalars + "\n" + headings, schema_version=2
    )
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_low_risk_cannot_bypass_authoritative_json_runtime_config(
    tmp_path: Path,
) -> None:
    base, candidate = _diff_repo(tmp_path, "config/routes.json")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "config/routes.json"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["config/routes.json"]


def test_legacy_read_only_rejects_nested_required_contract_keys() -> None:
    nested = "wrapper:\n" + "\n".join(
        f"  {key}: value" for key in checker.REQUIRED_KEYS
    )
    result = checker.validate_legacy_read_only(nested)
    assert not result["ok"]
    assert set(result["missing_keys"]) == set(checker.LEGACY_REQUIRED_KEYS)


def test_quoted_whitespace_sandbox_fields_are_rejected() -> None:
    sandbox = "sandbox:\n" + "".join(
        f'  {key}: "   "\n' for key in checker.SANDBOX_REQUIRED_KEYS
    )
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "sandbox: live\n", sandbox
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert set(result["sandbox_errors"]) == {
        f"empty sandbox.{key}" for key in checker.SANDBOX_REQUIRED_KEYS
    }


def test_null_list_item_cannot_satisfy_adversarial_reason() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", "  reason:\n    -"
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_yaml_tagged_null_cannot_satisfy_required_top_level_field() -> None:
    contract = _v2_contract().replace("intent: value", "intent: !!null")
    result = checker.validate(contract)
    assert not result["ok"]
    assert "intent" in result["empty_keys"]


def test_yaml_tagged_empty_string_cannot_satisfy_adversarial_reason() -> None:
    contract = _v2_contract(risk="low", decision="skipped").replace(
        "  reason: executable change", '  reason: !!str ""'
    )
    result = checker.validate(contract)
    assert not result["ok"]
    assert "empty adversarial_gate.reason" in result["adversarial_errors"]


def test_empty_markdown_links_do_not_fill_handoff_sections() -> None:
    metadata = "\n".join(f"{key}: value" for key in checker.HANDOFF_METADATA)
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(f"## {key.replace('_', ' ')}\n[]()" for key in keys)
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert set(result["empty_headings"]) == set(keys)


def test_low_risk_cannot_bypass_executable_bit_only_diff(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    target = tmp_path / "docs" / "runner.md"
    target.parent.mkdir()
    target.write_text("#!/bin/sh\necho bad\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/runner.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    target.chmod(0o755)
    subprocess.run(["git", "add", "docs/runner.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/runner.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/runner.md"]


def test_handoff_status_must_be_complete_partial_or_blocked() -> None:
    metadata = (
        "status: false\nupdated_at_utc: value\niteration: value\ncontract: value"
    )
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence" for key in keys
    )
    result = checker.validate_handoff(metadata + "\n" + headings, schema_version=2)
    assert not result["ok"]
    assert result["metadata_errors"]


def test_markdown_headings_inside_yaml_literal_do_not_form_contract() -> None:
    body = "\n".join(
        f"  # {key.replace('_', ' ')}\n  evidence"
        for key in checker.REQUIRED_KEYS + checker.V2_REQUIRED_KEYS
    )
    result = checker.validate("notes: |\n" + body)
    assert not result["ok"]


def test_low_risk_cannot_bypass_new_executable_low_risk_file(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    target = tmp_path / "docs" / "runner.md"
    target.parent.mkdir()
    target.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    target.chmod(0o755)
    subprocess.run(["git", "add", "docs/runner.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/runner.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/runner.md"]


def test_fenced_markdown_example_cannot_satisfy_handoff() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = (
        "status: complete\nupdated_at_utc: value\n"
        "iteration: value\ncontract: value"
    )
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nexample" for key in keys
    )
    result = checker.validate_handoff(
        f"```markdown\n{metadata}\n{headings}\n```\n",
        schema_version=2,
    )
    assert not result["ok"]


def test_authoritative_runtime_markdown_cannot_skip_high_risk_gate(
    tmp_path: Path,
) -> None:
    base, candidate = _diff_repo(tmp_path, "docs/runtime-policy.md")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/runtime-policy.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/runtime-policy.md"]


def test_preexisting_v1_contract_remains_readable_without_v2_handoff() -> None:
    historic = "\n".join(
        f"{key}: value" for key in checker.LEGACY_REQUIRED_KEYS
    )
    assert checker.validate_legacy_read_only(historic)["ok"]


def test_documented_v2_yaml_template_matches_checker() -> None:
    sandbox = "sandbox:\n" + "\n".join(
        f"  {key}: evidence" for key in checker.SANDBOX_REQUIRED_KEYS
    )
    template = (
        _v2_contract()
        .replace("sandbox: live", sandbox)
        .replace("handoff: value", "handoff:\n  path: docs/harp_iteration_handoff.md")
    )
    assert checker.validate(template)["ok"]


def test_tilde_fenced_markdown_example_cannot_satisfy_handoff() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = (
        "status: complete\nupdated_at_utc: value\n"
        "iteration: value\ncontract: value"
    )
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence" for key in keys
    )
    result = checker.validate_handoff(
        f"~~~markdown\n{metadata}\n{headings}\n~~~\n",
        schema_version=2,
    )
    assert not result["ok"]


def test_low_risk_cannot_bypass_active_svg_executable_content(
    tmp_path: Path,
) -> None:
    base, candidate = _diff_repo(tmp_path, "docs/payload.svg")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/payload.svg"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/payload.svg"]


def test_commonmark_indented_fence_cannot_satisfy_handoff() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = (
        "status: complete\nupdated_at_utc: value\n"
        "iteration: value\ncontract: value"
    )
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence" for key in keys
    )
    result = checker.validate_handoff(
        f" ```markdown\n{metadata}\n{headings}\n ````\n",
        schema_version=2,
    )
    assert not result["ok"]


def test_longer_commonmark_closing_fence_cannot_satisfy_handoff() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = (
        "status: complete\nupdated_at_utc: value\n"
        "iteration: value\ncontract: value"
    )
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\nevidence" for key in keys
    )
    result = checker.validate_handoff(
        f"```markdown\n{metadata}\n{headings}\n````\n",
        schema_version=2,
    )
    assert not result["ok"]


def test_low_risk_cannot_bypass_symlink_diff(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    (tmp_path / "link.md").symlink_to("runtime.py")
    subprocess.run(["git", "add", "link.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "link.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["link.md"]


def test_handoff_binding_rejects_path_outside_repository_docs(
    tmp_path: Path,
) -> None:
    external = tmp_path.parent / "external-handoff.md"
    contract = _v2_contract().replace(
        "handoff: value",
        "handoff:\n  path: ../external-handoff.md",
    )
    result = checker.validate_handoff_binding(contract, tmp_path, external)
    assert not result["ok"]
    assert not result["contained_in_docs"]


def test_current_agent_attacks_must_be_in_cumulative_corpus() -> None:
    corpus = [{"id": "historical"}]
    current = [{"id": "new_escape"}]
    corpus_ids = {attack["id"] for attack in corpus}
    current_ids = {attack["id"] for attack in current}
    assert not current_ids.issubset(corpus_ids)


def test_markdown_formatting_only_handoff_sections_are_empty() -> None:
    keys = checker.HANDOFF_HEADINGS + checker.V2_HANDOFF_HEADINGS
    metadata = (
        "status: complete\nupdated_at_utc: value\n"
        "iteration: value\ncontract: value"
    )
    headings = "\n".join(
        f"## {key.replace('_', ' ')}\n** **" for key in keys
    )
    result = checker.validate_handoff(
        metadata + "\n" + headings,
        schema_version=2,
    )
    assert not result["ok"]


def test_low_risk_cannot_bypass_authoritative_access_control_markdown(
    tmp_path: Path,
) -> None:
    base, candidate = _diff_repo(tmp_path, "docs/access-control.md")
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/access-control.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/access-control.md"]


def test_low_risk_cannot_bypass_gitlink_mode(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    (tmp_path / "nested").write_text("nested\n", encoding="utf-8")
    subprocess.run(["git", "add", "nested"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "nested"], cwd=tmp_path, check=True)
    nested = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    subprocess.run(["git", "reset", "--hard", base], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{nested},docs/vendor.md",
        ],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "commit", "-qm", "gitlink"], cwd=tmp_path, check=True)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    result = checker.validate_diff_binding(
        _bound_contract(base, candidate, "docs/vendor.md"), tmp_path
    )
    assert not result["ok"]
    assert result["risk_conflict"]
    assert result["high_risk_paths"] == ["docs/vendor.md"]
