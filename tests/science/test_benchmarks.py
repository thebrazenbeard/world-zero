from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError


def test_benchmark_cannot_claim_causal_topology_digest():
    from worldzero.science.benchmarks import BenchmarkManifest

    manifest = BenchmarkManifest(
        schema_version="BENCHMARK_V1",
        benchmark_id="B0_PERSISTENCE_TREND",
        method_class="PERSISTENCE_TREND",
        causal_interpretation=False,
        calibration_only_selection=True,
        final_holdout_access="FORBIDDEN_UNTIL_FINAL_EVALUATION",
        allowed_forms=("LAST_OBSERVATION",),
    )
    assert not hasattr(manifest, "topology_digest")
    with pytest.raises(ValidationError):
        BenchmarkManifest.model_validate(
            {**manifest.model_dump(), "topology_digest": "a" * 64}
        )


def test_b1_policy_is_calibration_only_and_noncausal():
    from worldzero.science.benchmarks import BenchmarkManifest

    b1 = BenchmarkManifest(
        schema_version="BENCHMARK_V1",
        benchmark_id="B1_REDUCED_FORM_EMPIRICAL",
        method_class="REDUCED_FORM_EMPIRICAL",
        causal_interpretation=False,
        calibration_only_selection=True,
        final_holdout_access="FORBIDDEN_UNTIL_FINAL_EVALUATION",
        feature_ids=("POPULATION", "ENERGY_INTENSITY"),
        hyperparameter_policy="NESTED_WITHIN_CALIBRATION",
        regularization_policy="PREREGISTERED_OR_CALIBRATION_SELECTED",
    )
    assert b1.calibration_only_selection is True
    assert b1.final_holdout_access == "FORBIDDEN_UNTIL_FINAL_EVALUATION"
    assert b1.causal_interpretation is False


def test_b1_rejects_causal_interpretation():
    from worldzero.science.benchmarks import BenchmarkManifest

    with pytest.raises(ValidationError):
        BenchmarkManifest(
            schema_version="BENCHMARK_V1",
            benchmark_id="B1_REDUCED_FORM_EMPIRICAL",
            method_class="REDUCED_FORM_EMPIRICAL",
            causal_interpretation=True,
            calibration_only_selection=True,
            final_holdout_access="FORBIDDEN_UNTIL_FINAL_EVALUATION",
            feature_ids=("POPULATION",),
            hyperparameter_policy="NESTED_WITHIN_CALIBRATION",
            regularization_policy="L2",
        )


def test_seed_benchmark_manifests_validate():
    from worldzero.science.benchmarks import BenchmarkManifest

    paths = [
        Path("benchmarks/B0_PERSISTENCE_TREND.yaml"),
        Path("benchmarks/B1_REDUCED_FORM_EMPIRICAL.yaml"),
    ]
    assert all(path.is_file() for path in paths)
    for path in paths:
        BenchmarkManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def test_benchmark_registry_rejects_duplicate_ids():
    from worldzero.science.benchmarks import BenchmarkManifest, BenchmarkRegistry

    benchmark = BenchmarkManifest(
        schema_version="BENCHMARK_V1",
        benchmark_id="B0_PERSISTENCE_TREND",
        method_class="PERSISTENCE_TREND",
        allowed_forms=("LAST_OBSERVATION",),
    )
    with pytest.raises(ValueError, match="duplicate benchmark id"):
        BenchmarkRegistry([benchmark, benchmark])
