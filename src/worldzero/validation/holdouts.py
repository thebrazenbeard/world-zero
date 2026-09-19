"""Explicit final-holdout selection from frozen evidence partitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from worldzero.data.observations import ObservationSeries
from worldzero.science.partitions import PartitionSet


@dataclass(frozen=True, slots=True)
class HoldoutSelection:
    partition_id: str
    partition_class: str
    observation_ids: tuple[str, ...]


def select_holdout(
    partition_set: PartitionSet,
    partition_id: str,
    *,
    observations: Mapping[str, ObservationSeries],
) -> HoldoutSelection:
    """Select a holdout only when every bound observation is validation eligible.

    Partition membership alone is not evidence eligibility. The caller must bind
    each partition observation ID to its governed typed ObservationSeries so
    projection/bridge/scenario inputs cannot become holdout evidence by ID alone.
    """
    for partition in partition_set.partitions:
        if partition.partition_id != partition_id:
            continue
        if partition.partition_class == "CALIBRATION":
            raise ValueError("calibration partition cannot be selected as a holdout")

        missing = sorted(set(partition.observation_ids) - set(observations))
        if missing:
            raise ValueError(
                "holdout observation(s) missing governed evidence binding: "
                + ", ".join(missing)
            )
        mismatched = sorted(
            observation_id
            for observation_id in partition.observation_ids
            if observations[observation_id].observable_id != observation_id
        )
        if mismatched:
            raise ValueError(
                "holdout observation binding identity mismatch: " + ", ".join(mismatched)
            )
        ineligible = sorted(
            observation_id
            for observation_id in partition.observation_ids
            if not observations[observation_id].validation_eligible
        )
        if ineligible:
            raise ValueError(
                "holdout observation(s) are not validation eligible: "
                + ", ".join(ineligible)
            )

        return HoldoutSelection(
            partition_id=partition.partition_id,
            partition_class=partition.partition_class,
            observation_ids=partition.observation_ids,
        )
    raise KeyError(f"unknown holdout partition: {partition_id}")
