"""Manifests for small derived datasets stored in Git."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .manifests import DatasetAdmissionStatus
from .observations import ObservationClass


class DerivedSourceBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DerivedDatasetManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_id: Literal["WORLD_ZERO_DERIVED_DATASET_MANIFEST_V1"]
    dataset_id: str = Field(min_length=1)
    source_lineage: tuple[DerivedSourceBinding, ...] = Field(min_length=1)
    transform_id: str = Field(min_length=1)
    transform_version: str = Field(min_length=1)
    transform_code_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str | None = Field(default=None, min_length=1)
    years: tuple[int, ...] = Field(min_length=1)
    unit: str = Field(min_length=1)
    observation_class: Literal["DERIVED"]
    source_observation_class: ObservationClass
    validation_eligible: bool
    output_path: str = Field(min_length=1)
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_length_bytes: int = Field(ge=1)
    generated_at: datetime
    admission_status: DatasetAdmissionStatus
    admission_record_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> DerivedDatasetManifest:
        if len(self.years) != len(set(self.years)):
            raise ValueError("derived dataset years must be unique")
        bridge_classes = {
            ObservationClass.NOWCAST,
            ObservationClass.PROJECTION,
            ObservationClass.SCENARIO_INPUT,
        }
        if self.source_observation_class in bridge_classes and self.validation_eligible:
            raise ValueError("bridge-derived data cannot be validation eligible")
        if (
            self.admission_status is DatasetAdmissionStatus.ADMITTED
            and not self.admission_record_id
        ):
            raise ValueError("ADMITTED derived dataset requires admission_record_id")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return self


def load_derived_dataset_manifest(path: Path) -> DerivedDatasetManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("derived dataset manifest must be a mapping")
    return DerivedDatasetManifest.model_validate(payload)
