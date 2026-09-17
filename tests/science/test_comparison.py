import pytest


def _subject(subject_id: str, subject_class: str = "CAUSAL_FAMILY"):
    from worldzero.science.comparison_protocol import ComparisonSubject

    return ComparisonSubject(subject_id=subject_id, subject_class=subject_class)


def _protocol():
    from worldzero.science.comparison_protocol import (
        ComparisonProtocol,
        DecisionRule,
        MetricSpec,
    )

    return ComparisonProtocol(
        schema_version="COMPARISON_PROTOCOL_V1",
        protocol_id="CP9",
        claim_id="C9",
        subjects=(
            _subject("F0_WORLD3_CONTROL"),
            _subject("F1_MARKET_ADAPTIVE"),
            _subject("F3_NET_ENERGY_MATERIAL"),
            _subject("B1_REDUCED_FORM_EMPIRICAL", "PREDICTIVE_BENCHMARK"),
        ),
        calibration_partition_id="CAL",
        holdout_partition_ids=("H1",),
        metrics=(
            MetricSpec(
                metric_id="RMSE",
                observable_ids=("POPULATION",),
                aggregation="MEAN",
                direction="LOWER_IS_BETTER",
            ),
        ),
        decision_rules=(
            DecisionRule(
                rule_id="R1",
                rule_type="BENCHMARK_MARGIN",
                metric_id="RMSE",
                threshold=0.0,
            ),
        ),
        missing_subject_policy="FAIL_COMPARISON",
        frozen_before_execution=True,
    )


def _result(subject_id: str, direction: str, rmse: float, subject_class: str = "CAUSAL_FAMILY"):
    from worldzero.science.comparison import FamilyRunResult

    return FamilyRunResult(
        subject_id=subject_id,
        subject_class=subject_class,
        direction=direction,
        metrics={"RMSE": rmse},
        valid=True,
    )


def _results():
    return {
        "F0_WORLD3_CONTROL": _result("F0_WORLD3_CONTROL", "SUPPORTED", 1.0),
        "F1_MARKET_ADAPTIVE": _result("F1_MARKET_ADAPTIVE", "SUPPORTED", 0.9),
        "F3_NET_ENERGY_MATERIAL": _result("F3_NET_ENERGY_MATERIAL", "SUPPORTED", 1.1),
        "B1_REDUCED_FORM_EMPIRICAL": _result(
            "B1_REDUCED_FORM_EMPIRICAL",
            "INDETERMINATE",
            1.2,
            "PREDICTIVE_BENCHMARK",
        ),
    }


def test_robust_label_requires_every_frozen_subject():
    from worldzero.science.comparison import compare

    results = _results()
    del results["F3_NET_ENERGY_MATERIAL"]
    with pytest.raises(ValueError, match="F3_NET_ENERGY_MATERIAL"):
        compare(_protocol(), results)


def test_disagreeing_valid_causal_families_are_family_sensitive():
    from worldzero.science.comparison import compare
    from worldzero.science.types import StructuralResultLabel

    results = _results()
    results["F3_NET_ENERGY_MATERIAL"].direction = "NOT_SUPPORTED"
    comparison = compare(_protocol(), results)
    assert comparison.structural_label == StructuralResultLabel.FAMILY_SENSITIVE


def test_agreeing_valid_causal_families_are_robust_within_declared_set():
    from worldzero.science.comparison import compare
    from worldzero.science.types import StructuralResultLabel

    comparison = compare(_protocol(), _results())
    assert comparison.structural_label == StructuralResultLabel.ROBUST_ACROSS_FAMILIES


def test_benchmark_can_outperform_all_causal_families():
    from worldzero.science.comparison import compare

    results = _results()
    results["B1_REDUCED_FORM_EMPIRICAL"].metrics["RMSE"] = 0.5
    comparison = compare(_protocol(), results)
    assert (
        comparison.benchmark_labels["B1_REDUCED_FORM_EMPIRICAL"]
        == "BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT"
    )


def test_benchmark_direction_does_not_change_causal_structural_label():
    from worldzero.science.comparison import compare
    from worldzero.science.types import StructuralResultLabel

    results = _results()
    results["B1_REDUCED_FORM_EMPIRICAL"].direction = "NOT_SUPPORTED"
    comparison = compare(_protocol(), results)
    assert comparison.structural_label == StructuralResultLabel.ROBUST_ACROSS_FAMILIES
