"""Frozen evidence partitions and holdout-leakage guards."""

from __future__ import annotations

from collections import Counter
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import content_digest

PartitionClass = Literal[
    "CALIBRATION",
    "INITIALIZATION",
    "TEMPORAL_HOLDOUT",
    "REGIONAL_HOLDOUT",
    "VARIABLE_HOLDOUT",
    "SHOCK_HOLDOUT",
    "NEGATIVE_CONTROL",
]


class EvidencePartition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    partition_id: str = Field(min_length=1)
    partition_class: PartitionClass
    observation_ids: tuple[str, ...] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def reject_duplicate_observations(self) -> EvidencePartition:
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError(f"duplicate observation ID within partition {self.partition_id}")
        return self


class PartitionSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    partition_set_id: str = Field(min_length=1)
    partitions: tuple[EvidencePartition, ...] = Field(min_length=2)
    frozen_before_execution: bool = True
    notes: str | None = None

    @model_validator(mode="after")
    def validate_partition_isolation(self) -> PartitionSet:
        partition_ids = [partition.partition_id for partition in self.partitions]
        duplicates = sorted(
            {partition_id for partition_id in partition_ids if partition_ids.count(partition_id) > 1}
        )
        if duplicates:
            raise ValueError("duplicate partition_id(s): " + ", ".join(duplicates))

        calibration = [
            partition for partition in self.partitions if partition.partition_class == "CALIBRATION"
        ]
        if len(calibration) != 1:
            raise ValueError("PartitionSet requires exactly one CALIBRATION partition")

        counts = Counter(
            observation_id
            for partition in self.partitions
            for observation_id in partition.observation_ids
        )
        multiply_assigned = sorted(
            observation_id for observation_id, count in counts.items() if count > 1
        )
        if multiply_assigned:
            raise ValueError(
                "observation ID assigned to multiple partitions; overlap: "
                + ", ".join(multiply_assigned)
            )

        assert_no_holdout_leakage(self.calibration_ids, self.final_holdout_ids)
        assert_no_initialization_holdout_leakage(
            self.initialization_ids,
            self.final_holdout_ids,
        )
        return self

    @property
    def calibration_ids(self) -> set[str]:
        calibration = next(
            partition for partition in self.partitions if partition.partition_class == "CALIBRATION"
        )
        return set(calibration.observation_ids)

    @property
    def initialization_ids(self) -> set[str]:
        return {
            observation_id
            for partition in self.partitions
            if partition.partition_class == "INITIALIZATION"
            for observation_id in partition.observation_ids
        }

    @property
    def final_holdout_ids(self) -> set[str]:
        holdout_classes = {
            "TEMPORAL_HOLDOUT",
            "REGIONAL_HOLDOUT",
            "VARIABLE_HOLDOUT",
            "SHOCK_HOLDOUT",
        }
        return {
            observation_id
            for partition in self.partitions
            if partition.partition_class in holdout_classes
            for observation_id in partition.observation_ids
        }

    @property
    def observation_ids(self) -> set[str]:
        return {
            observation_id
            for partition in self.partitions
            for observation_id in partition.observation_ids
        }

    def digest(self) -> str:
        return content_digest(self)


def assert_no_holdout_leakage(
    calibration_ids: AbstractSet[str] | set[str], final_holdout_ids: AbstractSet[str] | set[str]
) -> None:
    overlap = sorted(set(calibration_ids) & set(final_holdout_ids))
    if overlap:
        raise ValueError("calibration/final-holdout overlap: " + ", ".join(overlap))


def assert_no_initialization_holdout_leakage(
    initialization_ids: AbstractSet[str] | set[str],
    final_holdout_ids: AbstractSet[str] | set[str],
) -> None:
    overlap = sorted(set(initialization_ids) & set(final_holdout_ids))
    if overlap:
        raise ValueError("initialization/final-holdout overlap: " + ", ".join(overlap))


def load_partition_set(path: Path) -> PartitionSet:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("partition set must be a mapping")
    return PartitionSet.model_validate(payload)
