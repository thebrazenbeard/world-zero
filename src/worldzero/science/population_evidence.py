"""Exact historical population evidence catalogs and partition bindings."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.data.derived import DerivedDatasetManifest, load_derived_dataset_manifest
from worldzero.data.manifests import DatasetAdmissionStatus
from worldzero.science.partitions import PartitionSet
from worldzero.sectors.demography import AgeCohort


class PopulationEvidenceObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: str = Field(min_length=1)
    role: Literal["POPULATION_TOTAL", "POPULATION_COHORT"]
    dataset_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    year: int
    region_id: str = Field(min_length=1)
    cohort_id: str | None = None
    source_observation_class: Literal["OFFICIAL_ESTIMATE"]
    validation_eligible: Literal[True]
    evidence_covariance_group_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_role_coordinates(self) -> PopulationEvidenceObservation:
        if self.role == "POPULATION_TOTAL" and self.cohort_id is not None:
            raise ValueError("total-population observation cannot bind cohort_id")
        if self.role == "POPULATION_COHORT":
            if self.cohort_id is None:
                raise ValueError("cohort-population observation requires cohort_id")
            AgeCohort(self.cohort_id)
        return self


class PopulationEvidenceCatalog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WZ_POPULATION_EVIDENCE_CATALOG_V1"]
    catalog_id: str = Field(min_length=1)
    frozen_before_execution: Literal[True]
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str = Field(min_length=1)
    observations: tuple[PopulationEvidenceObservation, ...] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_unique_observation_ids(self) -> PopulationEvidenceCatalog:
        ids = [item.observation_id for item in self.observations]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ValueError(
                "duplicate population evidence observation ID(s): " + ", ".join(duplicates)
            )
        return self

    @property
    def observation_ids(self) -> set[str]:
        return {item.observation_id for item in self.observations}


def load_population_evidence_catalog(path: Path) -> PopulationEvidenceCatalog:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("population evidence catalog must be a mapping")
    return PopulationEvidenceCatalog.model_validate(payload)


def _resolve(root: Path, path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def verify_population_evidence_catalog(
    *,
    root: Path,
    catalog: PopulationEvidenceCatalog,
) -> PopulationEvidenceCatalog:
    cache: dict[str, tuple[DerivedDatasetManifest, list[dict[str, str]]]] = {}

    for observation in catalog.observations:
        if observation.manifest_path not in cache:
            manifest_path = _resolve(root, observation.manifest_path)
            manifest_bytes = manifest_path.read_bytes()
            if hashlib.sha256(manifest_bytes).hexdigest() != observation.manifest_sha256:
                raise ValueError("population evidence manifest digest mismatch")

            manifest = load_derived_dataset_manifest(manifest_path)
            output_path = _resolve(root, manifest.output_path)
            output_bytes = output_path.read_bytes()
            actual_output_sha256 = hashlib.sha256(output_bytes).hexdigest()
            if actual_output_sha256 != manifest.output_sha256:
                raise ValueError("population evidence output digest does not match manifest")
            if len(output_bytes) != manifest.output_length_bytes:
                raise ValueError("population evidence output length does not match manifest")

            rows = list(csv.DictReader(output_bytes.decode("utf-8").splitlines()))
            cache[observation.manifest_path] = (manifest, rows)

        manifest, rows = cache[observation.manifest_path]
        if manifest.dataset_id != observation.dataset_id:
            raise ValueError("population evidence dataset identity mismatch")
        if manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
            raise ValueError("population evidence dataset must be ADMITTED")
        if manifest.output_sha256 != observation.output_sha256:
            raise ValueError("population evidence catalog output digest mismatch")
        if manifest.years != (observation.year,):
            raise ValueError("population evidence year does not match manifest")
        if manifest.region_set_version != catalog.region_set_version:
            raise ValueError("population evidence region-set version mismatch")
        if manifest.source_observation_class.value != observation.source_observation_class:
            raise ValueError("population evidence source observation class mismatch")
        if manifest.validation_eligible != observation.validation_eligible:
            raise ValueError("population evidence validation eligibility mismatch")
        if observation.role == "POPULATION_COHORT":
            if manifest.cohort_set_version != catalog.cohort_set_version:
                raise ValueError("population evidence cohort-set version mismatch")
        elif manifest.cohort_set_version is not None:
            raise ValueError("total-population evidence must not bind a cohort set")

        matches = [
            row
            for row in rows
            if row.get("region_id") == observation.region_id
            and row.get("year") == str(observation.year)
            and (
                observation.role == "POPULATION_TOTAL"
                or row.get("cohort_id") == observation.cohort_id
            )
        ]
        if len(matches) != 1:
            raise ValueError("population evidence observation must resolve to exactly one row")
        row = matches[0]
        if row.get("source_observation_class") != observation.source_observation_class:
            raise ValueError("population evidence row source class mismatch")
        if row.get("observation_class") != "DERIVED":
            raise ValueError("population evidence row must be DERIVED")
        if row.get("validation_eligible") != "true":
            raise ValueError("population evidence row must remain validation eligible")
        if int(row["population_persons"]) <= 0:
            raise ValueError("population evidence value must be positive")

    return catalog



def verify_population_evidence_partition(
    *,
    catalog: PopulationEvidenceCatalog,
    partition_set: PartitionSet,
) -> PartitionSet:
    catalog_by_id = {item.observation_id: item for item in catalog.observations}
    assigned_ids = partition_set.calibration_ids | partition_set.final_holdout_ids
    catalog_ids = set(catalog_by_id)

    unknown_ids = sorted(assigned_ids - catalog_ids)
    if unknown_ids:
        raise ValueError(
            "population evidence partition references unknown observation ID(s): "
            + ", ".join(unknown_ids)
        )
    missing_ids = sorted(catalog_ids - assigned_ids)
    if missing_ids:
        raise ValueError(
            "population evidence catalog contains unassigned observation ID(s): "
            + ", ".join(missing_ids)
        )

    ineligible_holdouts = sorted(
        observation_id
        for observation_id in partition_set.final_holdout_ids
        if not catalog_by_id[observation_id].validation_eligible
    )
    if ineligible_holdouts:
        raise ValueError(
            "population evidence holdout contains non-validation-eligible observation ID(s): "
            + ", ".join(ineligible_holdouts)
        )

    return partition_set
