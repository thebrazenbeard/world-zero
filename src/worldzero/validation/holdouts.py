"""Explicit final-holdout selection from frozen evidence partitions."""

from __future__ import annotations

from dataclasses import dataclass

from worldzero.science.partitions import PartitionSet


@dataclass(frozen=True, slots=True)
class HoldoutSelection:
    partition_id: str
    partition_class: str
    observation_ids: tuple[str, ...]


def select_holdout(partition_set: PartitionSet, partition_id: str) -> HoldoutSelection:
    for partition in partition_set.partitions:
        if partition.partition_id != partition_id:
            continue
        if partition.partition_class == "CALIBRATION":
            raise ValueError("calibration partition cannot be selected as a holdout")
        return HoldoutSelection(
            partition_id=partition.partition_id,
            partition_class=partition.partition_class,
            observation_ids=partition.observation_ids,
        )
    raise KeyError(f"unknown holdout partition: {partition_id}")
