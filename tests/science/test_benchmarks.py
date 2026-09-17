import pytest

from worldzero.science.benchmarks import PredictiveBenchmarkV1


def b0_payload() -> dict:
    return {
        "schema_version": "PREDICTIVE_BENCHMARK_V1",
        "benchmark_id": "B0_POPULATION_TREND",
        "benchmark_kind": "B0_PERSISTENCE_TREND",
        "method": "LINEAR_TREND",
        "observable_ids": ["POPULATION"],
        "calibration_partition_id": "CAL_1900_1990",
        "holdout_partition_ids": ["HOLDOUT_1991_2020"],
        "causal_interpretation": False,
    }


def test_b0_contract_is_explicitly_noncausal():
    benchmark = PredictiveBenchmarkV1.model_validate(b0_payload())
    assert benchmark.causal_interpretation is False


def test_b0_rejects_reduced_form_features():
    payload = b0_payload()
    payload["feature_ids"] = ["GDP", "ENERGY"]
    with pytest.raises(ValueError, match="B0"):
        PredictiveBenchmarkV1.model_validate(payload)


def test_b1_requires_features_and_nested_tuning():
    payload = b0_payload()
    payload.update({
        "benchmark_id": "B1_REDUCED_FORM",
        "benchmark_kind": "B1_REDUCED_FORM_EMPIRICAL",
        "method": "REGULARIZED_VAR",
        "feature_ids": ["GDP", "ENERGY"],
        "nested_calibration_tuning": False,
    })
    with pytest.raises(ValueError, match="nested"):
        PredictiveBenchmarkV1.model_validate(payload)


def test_benchmark_digest_changes_with_method():
    benchmark = PredictiveBenchmarkV1.model_validate(b0_payload())
    changed = benchmark.model_copy(update={"method": "LOG_LINEAR_TREND"})
    assert benchmark.digest() != changed.digest()
