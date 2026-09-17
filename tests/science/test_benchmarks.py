from pathlib import Path

import pytest
import yaml

from worldzero.science.benchmarks import (
    BenchmarkManifest,
    BenchmarkRegistry,
    calibration_only_observation_ids,
)

ROOT = Path(__file__).parents[2]


def load_benchmark(name: str) -> BenchmarkManifest:
    payload = yaml.safe_load((ROOT / "benchmarks" / f"{name}.yaml").read_text(encoding="utf-8"))
    return BenchmarkManifest.model_validate(payload)


def test_benchmark_cannot_claim_causal_topology_digest():
    manifest = BenchmarkManifest(
        benchmark_id="B0_PERSISTENCE_TREND",
        method="PERSISTENCE",
        causal_interpretation=False,
    )
    assert not hasattr(manifest, "topology_digest")


def test_benchmark_causal_interpretation_is_forbidden():
    with pytest.raises(ValueError):
        BenchmarkManifest(
            benchmark_id="B1_REDUCED_FORM_EMPIRICAL",
            method="REGULARIZED_VAR",
            causal_interpretation=True,
        )


def test_b1_hyperparameter_search_uses_calibration_only():
    calibration = {"obs_1", "obs_2", "obs_3"}
    final_holdout = {"obs_4", "obs_5"}
    used_ids = calibration_only_observation_ids(calibration, final_holdout)
    assert used_ids == calibration
    assert used_ids.isdisjoint(final_holdout)


def test_hyperparameter_search_fails_if_calibration_and_holdout_overlap():
    with pytest.raises(ValueError, match="overlap"):
        calibration_only_observation_ids({"obs_1", "obs_2"}, {"obs_2", "obs_3"})


def test_b1_requires_frozen_feature_and_hyperparameter_policy():
    with pytest.raises(ValueError, match="feature_set"):
        BenchmarkManifest(
            benchmark_id="B1_REDUCED_FORM_EMPIRICAL",
            method="REGULARIZED_VAR",
            causal_interpretation=False,
            feature_set=(),
            hyperparameter_policy="nested calibration-only search",
        )


def test_benchmark_registry_rejects_duplicate_ids():
    b0 = BenchmarkManifest(
        benchmark_id="B0_PERSISTENCE_TREND",
        method="PERSISTENCE",
        causal_interpretation=False,
    )
    with pytest.raises(ValueError, match="duplicate"):
        BenchmarkRegistry([b0, b0])


def test_seed_benchmarks_parse_and_remain_noncausal():
    names = {path.stem for path in (ROOT / "benchmarks").glob("*.yaml")}
    assert names == {"B0_PERSISTENCE_TREND", "B1_REDUCED_FORM_EMPIRICAL"}
    manifests = [load_benchmark(name) for name in sorted(names)]
    assert all(not manifest.causal_interpretation for manifest in manifests)
    assert all(not hasattr(manifest, "topology_digest") for manifest in manifests)
