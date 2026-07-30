from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/delivery-alignment-iteration/SKILL.md"
text = SKILL.read_text(encoding="utf-8")
compact = " ".join(text.split())

checks = {
    "separate_repository_budgets": all(
        term in compact
        for term in (
            "tracked source",
            "generated/ignored checkout",
            "dependencies",
            "durable artifacts",
            "duplicate content",
            "Git object/history growth",
        )
    ),
    "one_authority_and_evidence_tiers": all(
        term in compact
        for term in (
            "Choose one authoritative form",
            "public reproducibility bundle",
            "bulky forensic evidence",
        )
    ),
    "responsibility_and_quality_ratchets": all(
        term in compact
        for term in (
            "pure state transitions",
            "policy decisions",
            "I/O adapters",
            "Ratchet quality debt",
        )
    ),
    "clean_room_and_destructive_authority": all(
        term in compact
        for term in (
            "fresh clone or equivalent exported tree",
            "explicit human authorization",
            "verified backup",
            "tested rollback",
        )
    ),
    "flow_diffusion_not_malicious_actor": all(
        term in compact
        for term in (
            "counterexample-seeking",
            "not an assumption that a malicious actor exists",
            "do not impose a one-perturbation rule",
            "Preserve generalization concerns",
        )
    ),
    "provider_free_boundary_supported": all(
        term in compact
        for term in (
            "provider-free deterministic system",
            "deterministic unreachability proof",
            "real non-provider boundary",
        )
    ),
    "safe_bounded_migration_extension": all(
        term in compact
        for term in (
            "deterministic replay proves",
            "one bounded replacement sunset",
            "Convenience or incomplete work is not an extension reason",
        )
    ),
    "generic_identity_not_harp_shaped": all(
        term in compact
        for term in (
            "project-declared injective typed subject identity",
            "other mechanisms must enumerate their own",
            "single canonical transition writer or transaction mechanism",
        )
    ),
    "harp_profile_remains_strict": all(
        term in compact
        for term in (
            "In HARP this is the typed-event supervisor transaction",
            "monotonic `event_seq`",
            "For HARP this includes",
            "For HARP this is the canonical reducer writer",
        )
    ),
}

failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{name}={'passed' if passed else 'failed'}")
raise SystemExit(1 if failed else 0)
