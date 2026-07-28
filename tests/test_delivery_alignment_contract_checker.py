from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


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
    )


def test_legacy_contract_remains_readable() -> None:
    assert checker.validate(_legacy_contract())["ok"]


def test_nested_contract_keys_do_not_satisfy_top_level_requirements() -> None:
    nested = "wrapper:\n" + "\n".join(
        f"  {key}: value" for key in checker.REQUIRED_KEYS
    )
    result = checker.validate(nested)
    assert not result["ok"]
    assert set(result["missing_keys"]) == set(checker.REQUIRED_KEYS)


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
    assert set(result["empty_keys"]) == set(checker.REQUIRED_KEYS)


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


def test_new_v1_contract_cannot_bypass_v2_rules() -> None:
    result = checker.validate(_legacy_contract())
    assert result["ok"]
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
