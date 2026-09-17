from pathlib import Path

import pytest
import yaml

from worldzero.science.families import FamilyRegistry, ModelFamilyManifest

ROOT = Path(__file__).parents[2]


def load_family(name: str) -> ModelFamilyManifest:
    payload = yaml.safe_load((ROOT / "model_families" / f"{name}.yaml").read_text(encoding="utf-8"))
    return ModelFamilyManifest.model_validate(payload)


def test_f0_rejects_market_price_feedback():
    f0 = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F0_WORLD3_CONTROL",
        status="DRAFT",
        causal_interpretation=True,
        required_mechanisms=("WORLD3_CORE",),
        forbidden_mechanisms=("SCARCITY_PRICE_FEEDBACK",),
    )
    with pytest.raises(ValueError, match="forbidden"):
        f0.validate_enabled_mechanisms({"WORLD3_CORE", "SCARCITY_PRICE_FEEDBACK"})


def test_family_rejects_missing_required_mechanism():
    f1 = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F1_MARKET_ADAPTIVE",
        status="DRAFT",
        causal_interpretation=True,
        required_mechanisms=("SCARCITY_PRICE_FEEDBACK", "DEMAND_RESPONSE"),
    )
    with pytest.raises(ValueError, match="required"):
        f1.validate_enabled_mechanisms({"SCARCITY_PRICE_FEEDBACK"})


def test_frozen_family_requires_exact_source_and_topology_bindings():
    with pytest.raises(ValueError, match="topology_digest"):
        ModelFamilyManifest(
            schema_version="MODEL_FAMILY_V1",
            family_id="F1_MARKET_ADAPTIVE",
            status="FROZEN_CANDIDATE",
            causal_interpretation=True,
            source_commit="a" * 40,
            topology_digest=None,
        )


def test_draft_family_may_defer_exact_source_binding_without_faking_digest():
    manifest = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F3_NET_ENERGY_MATERIAL",
        status="DRAFT",
        causal_interpretation=True,
    )
    assert manifest.topology_digest is None
    assert manifest.source_commit is None


def test_family_registry_rejects_duplicate_ids():
    f0 = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F0_WORLD3_CONTROL",
        status="DRAFT",
        causal_interpretation=True,
    )
    with pytest.raises(ValueError, match="duplicate"):
        FamilyRegistry([f0, f0])


def test_seed_family_manifests_are_only_f0_f1_f3_and_parse():
    family_dir = ROOT / "model_families"
    names = {path.stem for path in family_dir.glob("*.yaml")}
    assert names == {"F0_WORLD3_CONTROL", "F1_MARKET_ADAPTIVE", "F3_NET_ENERGY_MATERIAL"}
    manifests = [load_family(name) for name in sorted(names)]
    assert {m.family_id for m in manifests} == names


def test_f0_seed_forbids_modern_mechanisms_that_define_rivals():
    f0 = load_family("F0_WORLD3_CONTROL")
    assert "SCARCITY_PRICE_FEEDBACK" in f0.forbidden_mechanisms
    assert "DETAILED_NET_ENERGY_ACCOUNTING" in f0.forbidden_mechanisms
