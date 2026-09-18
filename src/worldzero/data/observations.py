"""Typed observation series with immutable raw-data lineage."""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObservationClass(StrEnum):
    DIRECT = "DIRECT"
    OFFICIAL_ESTIMATE = "OFFICIAL_ESTIMATE"
    NOWCAST = "NOWCAST"
    PROJECTION = "PROJECTION"
    DERIVED = "DERIVED"
    COMPOSITE = "COMPOSITE"
    SCENARIO_INPUT = "SCENARIO_INPUT"


class ObservationLineage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TransformRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    transform_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    code_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_observable_ids: tuple[str, ...] = Field(min_length=1)


class ObservationSeries(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observable_id: str = Field(min_length=1)
    observation_class: ObservationClass
    unit: str = Field(min_length=1)
    geography: tuple[str, ...] = Field(min_length=1)
    time: tuple[int, ...] = Field(min_length=1)
    values: tuple[float, ...] = Field(min_length=1)
    lineage: tuple[ObservationLineage, ...] = Field(min_length=1)
    validation_eligible: bool = True
    transform: TransformRecord | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_axes_and_transform(self) -> ObservationSeries:
        lengths = {len(self.geography), len(self.time), len(self.values)}
        if len(lengths) != 1:
            raise ValueError("observation geography/time/value axes must have equal length")
        if any(not item.strip() for item in self.geography):
            raise ValueError("observation geography IDs must be non-empty")
        if not all(math.isfinite(value) for value in self.values):
            raise ValueError("observation values must be finite")
        if self.observation_class is ObservationClass.DIRECT and self.transform is not None:
            raise ValueError("DIRECT observations cannot declare a transform")
        if (
            self.observation_class
            in {
                ObservationClass.NOWCAST,
                ObservationClass.PROJECTION,
                ObservationClass.SCENARIO_INPUT,
            }
            and self.validation_eligible
        ):
            raise ValueError(
                "bridge/projection/scenario-input observations cannot be validation eligible"
            )
        if (
            self.observation_class in {ObservationClass.DERIVED, ObservationClass.COMPOSITE}
            and self.transform is None
        ):
            raise ValueError("derived/composite observations require transform lineage")
        keys = [(item.dataset_id, item.content_sha256) for item in self.lineage]
        if len(keys) != len(set(keys)):
            raise ValueError("observation lineage entries must be unique")
        return self
