import pytest

from worldzero.science.partitions import (
    EvidencePartition,
    PartitionSet,
    assert_no_holdout_leakage,
    load_partition_set,
)


def partition(partition_id: str, partition_class: str, ids: set[str]):
    return EvidencePartition(
        partition_id=partition_id,
        partition_class=partition_class,
        observation_ids=tuple(sorted(ids)),
    )


def test_calibration_and_final_holdout_cannot_overlap():
    with pytest.raises(ValueError, match="overlap"):
        assert_no_holdout_leakage({"x", "y"}, {"y", "z"})


def test_partition_set_rejects_calibration_holdout_leakage():
    with pytest.raises(ValueError, match="overlap"):
        PartitionSet(
            partition_set_id="P1",
            partitions=(
                partition("CAL", "CALIBRATION", {"obs_1", "obs_2"}),
                partition("HOLD", "TEMPORAL_HOLDOUT", {"obs_2", "obs_3"}),
            ),
        )


def test_partition_set_requires_exactly_one_calibration_partition():
    with pytest.raises(ValueError, match="exactly one CALIBRATION"):
        PartitionSet(
            partition_set_id="P1",
            partitions=(
                partition("HOLD1", "TEMPORAL_HOLDOUT", {"obs_3"}),
                partition("HOLD2", "SHOCK_HOLDOUT", {"obs_4"}),
            ),
        )


def test_duplicate_partition_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate partition_id"):
        PartitionSet(
            partition_set_id="P1",
            partitions=(
                partition("SAME", "CALIBRATION", {"obs_1"}),
                partition("SAME", "TEMPORAL_HOLDOUT", {"obs_2"}),
            ),
        )


def test_partition_observation_ids_are_unique():
    with pytest.raises(ValueError, match="duplicate observation"):
        EvidencePartition(
            partition_id="CAL",
            partition_class="CALIBRATION",
            observation_ids=("obs_1", "obs_1"),
        )


def test_partition_set_exposes_calibration_and_final_holdout_ids():
    partitions = PartitionSet(
        partition_set_id="P1",
        partitions=(
            partition("CAL", "CALIBRATION", {"obs_1", "obs_2"}),
            partition("TEMP", "TEMPORAL_HOLDOUT", {"obs_3"}),
            partition("SHOCK", "SHOCK_HOLDOUT", {"obs_4"}),
        ),
    )
    assert partitions.calibration_ids == {"obs_1", "obs_2"}
    assert partitions.final_holdout_ids == {"obs_3", "obs_4"}


def test_partition_classes_are_closed():
    with pytest.raises(ValueError):
        partition("BAD", "TRAININGISH", {"obs_1"})



def test_partition_set_loads_frozen_yaml(tmp_path):
    path = tmp_path / "partitions.yaml"
    path.write_text(
        "partition_set_id: P1\n"
        "frozen_before_execution: true\n"
        "partitions:\n"
        "  - partition_id: CAL\n"
        "    partition_class: CALIBRATION\n"
        "    observation_ids: [obs_1]\n"
        "  - partition_id: HOLD\n"
        "    partition_class: VARIABLE_HOLDOUT\n"
        "    observation_ids: [obs_2]\n",
        encoding="utf-8",
    )
    loaded = load_partition_set(path)
    assert loaded.partition_set_id == "P1"
    assert loaded.calibration_ids == {"obs_1"}
    assert loaded.final_holdout_ids == {"obs_2"}
