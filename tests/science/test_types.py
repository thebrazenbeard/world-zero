from worldzero.science.types import (
    AdmissionDisposition,
    BenchmarkResultLabel,
    ControlMode,
    EvidenceClass,
    IdentifiabilityClass,
    StructuralResultLabel,
)


def test_evidence_classes_are_exact():
    assert {x.value for x in EvidenceClass} == {
        "OBSERVED", "DERIVED", "INFERRED", "HYPOTHESIS",
        "DISPUTED", "UNKNOWN", "SUPERSEDED",
    }


def test_control_modes_are_exact():
    assert {x.value for x in ControlMode} == {
        "ENDOGENOUS", "EXOGENOUS_TRAJECTORY",
        "INTERVENTION_CONTROLLED", "ABSENT",
    }


def test_structural_result_labels_are_exact():
    assert {x.value for x in StructuralResultLabel} == {
        "ROBUST_ACROSS_FAMILIES", "FAMILY_SENSITIVE", "IDENTIFICATION_LIMITED",
        "CONTROL_ONLY", "UNKNOWN",
    }


def test_benchmark_result_labels_are_exact():
    assert {x.value for x in BenchmarkResultLabel} == {
        "OUTPERFORMS_B0_ON_DECLARED_HOLDOUT",
        "OUTPERFORMS_B1_ON_DECLARED_HOLDOUT",
        "NO_PREDICTIVE_GAIN_OVER_BENCHMARK",
        "BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT",
        "INTERVENTION_COMPARISON_NOT_APPLICABLE_TO_BENCHMARK",
    }


def test_identifiability_classes_are_exact():
    assert {x.value for x in IdentifiabilityClass} == {
        "IDENTIFIABLE_ENOUGH_FOR_TEST", "WEAKLY_IDENTIFIABLE",
        "UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE", "OBSERVATION_MODEL_INADEQUATE",
    }


def test_admission_dispositions_are_exact():
    assert {x.value for x in AdmissionDisposition} == {
        "RESEARCH_ONLY", "RIVAL_FAMILY_ONLY", "ADMITTED_COMPONENT",
        "F7_CANDIDATE", "F7_ADMITTED", "REJECTED", "SUPERSEDED",
        "UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE",
    }
