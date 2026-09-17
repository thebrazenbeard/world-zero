import pytest


def _partition(partition_id: str, partition_class: str, *ids: str):
    from worldzero.science.partitions import EvidencePartition

    return EvidencePartition(
        partition_id=partition_id,
        partition_class=partition_class,
        observation_ids=frozenset(ids),
    )


def test_calibration_and_final_holdout_cannot_overlap():
    from worldzero.science.partitions import assert_no_holdout_leakage

    with pytest.raises(ValueError, match="overlap"):
        assert_no_holdout_leakage({"x", "y"}, {"y", "z"})


def test_partition_set_exposes_calibration_and_final_holdout_ids():
    from worldzero.science.partitions import PartitionSet

    partitions = PartitionSet(
        partition_set_id="P1",
        partitions=(
            _partition("cal", "CALIBRATION", "a", "b"),
            _partition("future", "TEMPORAL_HOLDOUT", "c"),
            _partition("region", "REGIONAL_HOLDOUT", "d"),
            _partition("negative", "NEGATIVE_CONTROL", "n"),
        ),
    )
    assert partitions.calibration_ids == frozenset({"a", "b"})
    assert partitions.final_holdout_ids == frozenset({"c", "d"})
    assert partitions.negative_control_ids == frozenset({"n"})


def test_partition_set_rejects_calibration_holdout_overlap():
    from worldzero.science.partitions import PartitionSet

    with pytest.raises(ValueError, match="overlap"):
        PartitionSet(
            partition_set_id="P1",
            partitions=(
                _partition("cal", "CALIBRATION", "same"),
                _partition("future", "TEMPORAL_HOLDOUT", "same"),
            ),
        )


def test_partition_set_rejects_duplicate_partition_ids():
    from worldzero.science.partitions import PartitionSet

    with pytest.raises(ValueError, match="duplicate partition id"):
        PartitionSet(
            partition_set_id="P1",
            partitions=(
                _partition("dup", "CALIBRATION", "a"),
                _partition("dup", "TEMPORAL_HOLDOUT", "b"),
            ),
        )


def test_b1_hyperparameter_search_uses_calibration_only():
    from worldzero.science.benchmarks import BenchmarkManifest
    from worldzero.science.partitions import PartitionSet

    b1 = BenchmarkManifest(
        schema_version="BENCHMARK_V1",
        benchmark_id="B1_REDUCED_FORM_EMPIRICAL",
        method_class="REDUCED_FORM_EMPIRICAL",
        feature_ids=("POPULATION",),
        hyperparameter_policy="NESTED_WITHIN_CALIBRATION",
        regularization_policy="L2",
    )
    partitions = PartitionSet(
        partition_set_id="P1",
        partitions=(
            _partition("cal", "CALIBRATION", "a", "b"),
            _partition("future", "TEMPORAL_HOLDOUT", "c", "d"),
        ),
    )
    used_ids = b1.hyperparameter_search_observation_ids(partitions)
    assert used_ids == frozenset({"a", "b"})
    assert used_ids.isdisjoint(partitions.final_holdout_ids)
