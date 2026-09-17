from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from worldzero.science.mechanisms import MechanismAdmission, MechanismRegistry
from worldzero.science.types import AdmissionDisposition, EvidenceClass, IdentifiabilityClass


def _mechanism(mechanism_id: str) -> MechanismAdmission:
    return MechanismAdmission(
        mechanism_id=mechanism_id,
        proposition=f"Test mechanism {mechanism_id}",
        evidence_class=EvidenceClass.HYPOTHESIS,
        identifiability=IdentifiabilityClass.WEAKLY_IDENTIFIABLE,
        disposition=AdmissionDisposition.RIVAL_FAMILY_ONLY,
        null_or_rival="NULL",
    )


def test_f0_rejects_market_price_feedback():
    from worldzero.science.families import ModelFamilyManifest

    registry = MechanismRegistry(
        [_mechanism("WORLD3_CORE"), _mechanism("SCARCITY_PRICE_FEEDBACK")]
    )
    f0 = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F0_WORLD3_CONTROL",
        family_name="World3-compatible control",
        status="DRAFT",
        enabled_mechanism_ids=("WORLD3_CORE",),
        required_mechanism_ids=("WORLD3_CORE",),
        forbidden_mechanism_ids=("SCARCITY_PRICE_FEEDBACK",),
    )
    with pytest.raises(ValueError, match="forbidden"):
        f0.validate_enabled_mechanisms(
            {"WORLD3_CORE", "SCARCITY_PRICE_FEEDBACK"}, registry
        )


def test_non_draft_family_requires_real_topology_digest():
    from worldzero.science.families import ModelFamilyManifest

    with pytest.raises(ValidationError, match="topology_digest"):
        ModelFamilyManifest(
            schema_version="MODEL_FAMILY_V1",
            family_id="F1_MARKET_ADAPTIVE",
            family_name="Market adaptive",
            status="FROZEN_CANDIDATE",
            enabled_mechanism_ids=("SCARCITY_PRICE_FEEDBACK",),
            required_mechanism_ids=("SCARCITY_PRICE_FEEDBACK",),
        )


def test_seed_family_manifests_validate():
    from worldzero.science.families import ModelFamilyManifest

    paths = [
        Path("model_families/F0_WORLD3_CONTROL.yaml"),
        Path("model_families/F1_MARKET_ADAPTIVE.yaml"),
        Path("model_families/F3_NET_ENERGY_MATERIAL.yaml"),
    ]
    assert all(path.is_file() for path in paths)
    for path in paths:
        ModelFamilyManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def test_family_registry_rejects_duplicate_ids():
    from worldzero.science.families import FamilyRegistry, ModelFamilyManifest

    family = ModelFamilyManifest(
        schema_version="MODEL_FAMILY_V1",
        family_id="F0_WORLD3_CONTROL",
        family_name="World3-compatible control",
        status="DRAFT",
        enabled_mechanism_ids=("WORLD3_CORE",),
        required_mechanism_ids=("WORLD3_CORE",),
    )
    with pytest.raises(ValueError, match="duplicate family id"):
        FamilyRegistry([family, family])
