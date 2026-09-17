import importlib
import importlib.util

import pytest


def _types_module():
    if importlib.util.find_spec("worldzero.science.types") is None:
        pytest.fail("worldzero.science.types is not implemented")
    return importlib.import_module("worldzero.science.types")


def test_evidence_classes_are_exact():
    module = _types_module()
    assert {x.value for x in module.EvidenceClass} == {
        "OBSERVED",
        "DERIVED",
        "INFERRED",
        "HYPOTHESIS",
        "DISPUTED",
        "UNKNOWN",
        "SUPERSEDED",
    }


def test_control_modes_are_exact():
    module = _types_module()
    assert {x.value for x in module.ControlMode} == {
        "ENDOGENOUS",
        "EXOGENOUS_TRAJECTORY",
        "INTERVENTION_CONTROLLED",
        "ABSENT",
    }
