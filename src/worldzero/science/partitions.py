from __future__ import annotations

from collections.abc import Set as AbstractSet
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PartitionClass = Literal[
    "CALIBRATION",
    "TEMPORAL_HOLDOUT",
    "REGIONAL_HOLDOUT",
    "VARIABLE_HOLDOUT",
    "SHOCK_HOLDOUT",
    "NEGATIVE_CONTROL",
]

_FINAL_HOLDOUT_CLASSES = frozenset(
    {
        "TEMPORAL_HOLDOUT",
        "REGIONAL_HOLDOUT",
        "VARIABLE_HOLDOUT",
        "SHOCK_HOLDOUT",
    }
)


def assert_no_holdout_leakage(
    calibration_ids: AbstractSet[str],
    final_holdout_ids: AbstractSet[str],
) -> None:
    overlap = set(calibration_ids) & set(final_holdout_ids)
    if overlap:
        raise ValueError(
            "calibration/final-holdout overlap: " + ", ".join(sorted(overlap))
        )


class EvidencePartition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    partition_id: str = Field(min_length=1)
    partition_class: PartitionClass
    observation_ids: frozenset[str] = Field(min_length=1)


class PartitionSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    partition_set_id: str = Field(min_length=1)
    partitions: tuple[EvidencePartition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_partitions(self) -> PartitionSet:
        partition_ids = [partition.partition_id for partition in self.partitions]
        if len(partition_ids) != len(set(partition_ids)):
            raise ValueError("duplicate partition id")
        if not any(
            partition.partition_class == "CALIBRATION" for partition in self.partitions
        ):
            raise ValueError("partition set requires a CALIBRATION partition")
        assert_no_holdout_leakage(self.calibration_ids, self.final_holdout_ids)
        return self

    @property
    def calibration_ids(self) -> frozenset[str]:
        return frozenset(
            observation_id
            for partition in self.partitions
            if partition.partition_class == "CALIBRATION"
            for observation_id in partition.observation_ids
        )

    @property
    def final_holdout_ids(self) -> frozenset[str]:
        return frozenset(
            observation_id
            for partition in self.partitions
            if partition.partition_class in _FINAL_HOLDOUT_CLASSES
            for observation_id in partition.observation_ids
        )

    @property
    def negative_control_ids(self) -> frozenset[str]:
        return frozenset(
            observation_id
            for partition in self.partitions
            if partition.partition_class == "NEGATIVE_CONTROL"
            for observation_id in partition.observation_ids
        )
