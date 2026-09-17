import importlib
import importlib.util

import pytest


def _mechanisms():
    if importlib.util.find_spec("worldzero.science.mechanisms") is None:
        pytest.fail("worldzero.science.mechanisms is not implemented")
    return importlib.import_module("worldzero.science.mechanisms")


def rival_only(module):
    return module.MechanismAdmission(
        mechanism_id="THRESHOLD_X",
        proposition="Subsystem may switch regime above a stress threshold.",
        evidence_class="HYPOTHESIS",
        identifiability="UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE",
        disposition="RIVAL_FAMILY_ONLY",
        null_or_rival="Smooth response without a threshold.",
        kill_test_id="KT_THRESHOLD_X",
        ablation_expectation="Smooth null remains available.",
        numerical_integrity="NOT_RUN",
    )


def test_unidentifiable_mechanism_can_remain_rival_only():
    module = _mechanisms()
    mechanism = rival_only(module)
    assert mechanism.disposition.value == "RIVAL_FAMILY_ONLY"


def test_f7_rejects_missing_holdout_or_invariant_target():
    module = _mechanisms()
    mechanism = module.MechanismAdmission(
        mechanism_id="INCOMPLETE",
        proposition="An incomplete candidate.",
        evidence_class="INFERRED",
        identifiability="WEAKLY_IDENTIFIABLE",
        disposition="F7_CANDIDATE",
        null_or_rival="Null relation.",
        kill_test_id="KT_INCOMPLETE",
        ablation_expectation="Output changes when disabled.",
        complexity_dynamic_states=1,
        calibrated_parameter_count=1,
        numerical_integrity="PASS",
        unresolved_negative_transfer_count=0,
    )
    registry = module.MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="holdout"):
        module.assert_f7_admissible(["INCOMPLETE"], registry)


def test_f7_rejects_unidentifiable_non_invariant_mechanism():
    module = _mechanisms()
    mechanism = rival_only(module).model_copy(
        update={
            "disposition": module.AdmissionDisposition.F7_CANDIDATE,
            "holdout_target": "held-out regime transitions",
            "numerical_integrity": "PASS",
        }
    )
    registry = module.MechanismRegistry([mechanism])
    with pytest.raises(ValueError, match="identifiability"):
        module.assert_f7_admissible(["THRESHOLD_X"], registry)


def test_valid_f7_candidate_passes_admission():
    module = _mechanisms()
    mechanism = module.MechanismAdmission(
        mechanism_id="SCARCITY_RESPONSE",
        proposition="Observed scarcity can alter demand and investment response.",
        evidence_class="INFERRED",
        identifiability="WEAKLY_IDENTIFIABLE",
        disposition="F7_CANDIDATE",
        null_or_rival="No adaptive scarcity response.",
        kill_test_id="KT_SCARCITY_RESPONSE",
        holdout_target="held-out shortage episodes",
        ablation_expectation="Holdout shortage response worsens when disabled.",
        complexity_dynamic_states=1,
        calibrated_parameter_count=2,
        numerical_integrity="PASS",
        unresolved_negative_transfer_count=0,
    )
    registry = module.MechanismRegistry([mechanism])
    admitted = module.assert_f7_admissible(["SCARCITY_RESPONSE"], registry)
    assert admitted == (mechanism,)
