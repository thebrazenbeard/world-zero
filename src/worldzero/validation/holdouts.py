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


def _validate_initialization_observation_ids(values: tuple[str, ...]) -> None:
    if type(values) is not tuple or any(
        type(value) is not str or not value for value in values
    ):
        raise ValueError(
            "initialization observation IDs must be an exact tuple of non-empty str values"
        )
    if len(values) != len(set(values)):
        raise ValueError("initialization observation IDs must be unique")


def select_holdout(
    partition_set: PartitionSet,
    partition_id: str,
    *,
    observations: Mapping[str, ObservationSeries],
    initialization_observation_ids: tuple[str, ...],
) -> HoldoutSelection:
    """Select a holdout only when every bound observation is validation eligible.

    Partition membership alone is not evidence eligibility. The caller must bind
    each partition observation ID to its governed typed ObservationSeries so
    projection/bridge/scenario inputs cannot become holdout evidence by ID alone.

    The caller must also declare the exact governed observation IDs consumed while
    constructing the initial model state. A final holdout cannot contain any of
    those IDs. An empty tuple means the initial state consumed no governed
    observation IDs; it must not be used to mean "unknown".
    """
    _validate_initialization_observation_ids(initialization_observation_ids)

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

        initialization_overlap = sorted(
            set(partition.observation_ids) & set(initialization_observation_ids)
        )
        if initialization_overlap:
            raise ValueError(
                "holdout observation(s) were consumed during initialization: "
                + ", ".join(initialization_overlap)
            )

        return HoldoutSelection(
            partition_id=partition.partition_id,
            partition_class=partition.partition_class,
            observation_ids=partition.observation_ids,
        )
    raise KeyError(f"unknown holdout partition: {partition_id}")
