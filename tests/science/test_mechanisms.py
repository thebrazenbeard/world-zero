import pytest

from worldzero.science.mechanisms import (
    ComplexityCost,
    MechanismAdmission,
    MechanismRegistry,
    assert_f7_admissible,
)
from worldzero.science.types import AdmissionDisposition, EvidenceClass, IdentifiabilityClass


def admissible_mechanism(mechanism_id="M_OK"):
    return MechanismAdmission(
        mechanism_id=mechanism_id,
        proposition="A bounded mechanism changes the target under a specified condition.",
        affected_object_ids=("DEMAND_RESPONSE",),
        interpretation="Synthetic test mechanism.",
        units_and_conservation="No conserved stock is created or destroyed.",
        evidence_class=EvidenceClass.INFERRED,
        clarity_pass=True,
        source_ids=("SRC_A",),
        rival_or_null="NULL_RESPONSE",
        uncertainty="Parameter and structural uncertainty remain.",
        identifiability=IdentifiabilityClass.WEAKLY_IDENTIFIABLE,
        motivating_residual="Held-out residual under the target shock.",
        kill_test_id="KT_M_OK",
        kill_test_survived=True,
        holdout_target="SHOCK_HOLDOUT",
        holdout_or_invariant_value_pass=True,
        ablation_expectation="Removing the mechanism worsens the preregistered target.",
        ablation_value_pass=True,
        structural_rival_analysis="The target is compared under a simpler null relation.",
        complexity=ComplexityCost(dynamic_states=1, calibrated_parameters=1),
        complexity_proportionate=True,
        numerical_integrity="PASS",
        unresolved_negative_transfer_defects=(),
        disposition=AdmissionDisposition.F7_CANDIDATE,
    )


def test_unidentifiable_mechanism_can_remain_rival_only():
    mechanism = MechanismAdmission(
        mechanism_id="THRESHOLD_X",
        proposition="Subsystem may switch regime above stress threshold.",
        affected_object_ids=("THRESHOLD_STATE",),
        interpretation="Alternative structural threshold.",
        units_and_conservation="No conservation exception claimed.",
        evidence_class=EvidenceClass.HYPOTHESIS,
        clarity_pass=True,
        source_ids=(),
        rival_or_null="SMOOTH_NULL",
        uncertainty="Threshold location is structurally uncertain.",
        identifiability=IdentifiabilityClass.UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE,
        motivating_residual=None,
        kill_test_id="KT_THRESHOLD_X",
        kill_test_survived=False,
        holdout_target=None,
        invariant_target=None,
        holdout_or_invariant_value_pass=False,
        ablation_expectation="Smooth null remains available.",
        ablation_value_pass=False,
        structural_rival_analysis="Threshold and smooth rivals remain explicit.",
        complexity=ComplexityCost(dynamic_states=1, calibrated_parameters=1),
        complexity_proportionate=False,
        numerical_integrity="UNKNOWN",
        disposition=AdmissionDisposition.RIVAL_FAMILY_ONLY,
    )
    assert mechanism.disposition is AdmissionDisposition.RIVAL_FAMILY_ONLY


def test_f7_rejects_failed_clarity_gate():
    mechanism = admissible_mechanism().model_copy(update={"clarity_pass": False}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="clarity"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_failed_kill_test():
    mechanism = admissible_mechanism().model_copy(update={"kill_test_survived": False}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="kill test"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_holdout_or_invariant_value():
    mechanism = admissible_mechanism().model_copy(
        update={"holdout_or_invariant_value_pass": False}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="holdout/invariant value"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_ablation_value():
    mechanism = admissible_mechanism().model_copy(update={"ablation_value_pass": False}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="ablation value"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_holdout_or_invariant_target():
    mechanism = admissible_mechanism().model_copy(
        update={"holdout_target": None, "invariant_target": None}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="holdout or invariant target"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_unidentifiable_non_invariant_mechanism():
    mechanism = admissible_mechanism().model_copy(
        update={"identifiability": IdentifiabilityClass.UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE},
        deep=True,
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="identifiability"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_hard_invariant_can_use_identifiability_exception():
    mechanism = admissible_mechanism("M_INVARIANT").model_copy(
        update={
            "identifiability": IdentifiabilityClass.UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE,
            "hard_invariant_required": True,
            "holdout_target": None,
            "invariant_target": "GLOBAL_ENERGY_BALANCE",
        },
        deep=True,
    )
    registry = MechanismRegistry([mechanism])
    assert_f7_admissible([mechanism.mechanism_id], registry)


def test_invariant_exception_requires_explicit_invariant_target():
    mechanism = admissible_mechanism("M_BAD_INVARIANT").model_copy(
        update={
            "identifiability": IdentifiabilityClass.UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE,
            "hard_invariant_required": True,
            "holdout_target": "ORDINARY_HOLDOUT",
            "invariant_target": None,
        },
        deep=True,
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="explicit invariant target"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_kill_test():
    mechanism = admissible_mechanism().model_copy(update={"kill_test_id": None}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="kill test"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_ablation_expectation():
    mechanism = admissible_mechanism().model_copy(update={"ablation_expectation": None}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="ablation"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_missing_structural_rival_analysis():
    mechanism = admissible_mechanism().model_copy(
        update={"structural_rival_analysis": None}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="structural rival"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_disproportionate_complexity():
    mechanism = admissible_mechanism().model_copy(
        update={"complexity_proportionate": False}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="complexity"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_numerical_integrity_failure():
    mechanism = admissible_mechanism().model_copy(update={"numerical_integrity": "FAIL"}, deep=True)
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="numerical integrity"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_unresolved_negative_transfer():
    mechanism = admissible_mechanism().model_copy(
        update={"unresolved_negative_transfer_defects": ("CARBON_BALANCE_DRIFT",)}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="negative-transfer"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_f7_rejects_non_f7_disposition_even_when_other_gates_pass():
    mechanism = admissible_mechanism().model_copy(
        update={"disposition": AdmissionDisposition.RIVAL_FAMILY_ONLY}, deep=True
    )
    registry = MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="disposition"):
        assert_f7_admissible([mechanism.mechanism_id], registry)


def test_registry_rejects_duplicate_mechanism_ids():
    mechanism = admissible_mechanism()
    with pytest.raises(ValueError, match="duplicate"):
        MechanismRegistry([mechanism, mechanism])


def test_f7_rejects_unknown_mechanism_id():
    registry = MechanismRegistry([admissible_mechanism()])
    with pytest.raises(KeyError, match="MISSING"):
        assert_f7_admissible(["MISSING"], registry)


def test_admissible_mechanism_passes_f7_gate():
    mechanism = admissible_mechanism()
    registry = MechanismRegistry([mechanism])
    assert_f7_admissible([mechanism.mechanism_id], registry)
