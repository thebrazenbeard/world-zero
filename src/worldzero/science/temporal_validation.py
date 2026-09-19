"""Governed temporal population-validation subjects."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.population_evidence import PopulationEvidenceCatalog


class TemporalPopulationValidationSubject(BaseModel):
    """Freeze the evidence identity for a pre-state -> future-holdout experiment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WZ_TEMPORAL_POPULATION_VALIDATION_SUBJECT_V1"]
    subject_id: str = Field(min_length=1)
    frozen_before_execution: Literal[True]
    initialization_catalog_id: str = Field(min_length=1)
    holdout_catalog_id: str = Field(min_length=1)
    initialization_year: int
    holdout_year: int
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str = Field(min_length=1)
    initialization_observation_ids: tuple[str, ...] = Field(min_length=1)
    holdout_observation_ids: tuple[str, ...] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_temporal_isolation(self) -> TemporalPopulationValidationSubject:
        if self.holdout_year <= self.initialization_year:
            raise ValueError("holdout year must be strictly after initialization year")

        initialization_ids = self.initialization_observation_ids
        holdout_ids = self.holdout_observation_ids
        if len(initialization_ids) != len(set(initialization_ids)):
            raise ValueError("duplicate initialization observation ID")
        if len(holdout_ids) != len(set(holdout_ids)):
            raise ValueError("duplicate holdout observation ID")

        overlap = sorted(set(initialization_ids) & set(holdout_ids))
        if overlap:
            raise ValueError(
                "initialization/temporal-holdout overlap: " + ", ".join(overlap)
            )
        return self


def _cohort_ids_for_year(
    catalog: PopulationEvidenceCatalog,
    year: int,
) -> set[str]:
    return {
        item.observation_id
        for item in catalog.observations
        if item.role == "POPULATION_COHORT" and item.year == year
    }


def verify_temporal_population_validation_subject(
    *,
    subject: TemporalPopulationValidationSubject,
    initialization_catalog: PopulationEvidenceCatalog,
    holdout_catalog: PopulationEvidenceCatalog,
) -> TemporalPopulationValidationSubject:
    """Fail closed unless the subject binds complete governed cohort cuts."""

    if initialization_catalog.catalog_id != subject.initialization_catalog_id:
        raise ValueError("initialization catalog identity mismatch")
    if holdout_catalog.catalog_id != subject.holdout_catalog_id:
        raise ValueError("holdout catalog identity mismatch")

    for catalog in (initialization_catalog, holdout_catalog):
        if catalog.region_set_version != subject.region_set_version:
            raise ValueError("temporal subject region-set version mismatch")
        if catalog.cohort_set_version != subject.cohort_set_version:
            raise ValueError("temporal subject cohort-set version mismatch")
        if not catalog.frozen_before_execution:
            raise ValueError("temporal evidence catalog must be frozen before execution")

    expected_initialization_ids = _cohort_ids_for_year(
        initialization_catalog,
        subject.initialization_year,
    )
    expected_holdout_ids = _cohort_ids_for_year(
        holdout_catalog,
        subject.holdout_year,
    )
    if not expected_initialization_ids:
        raise ValueError("initialization catalog has no governed cohort observations for year")
    if not expected_holdout_ids:
        raise ValueError("holdout catalog has no governed cohort observations for year")

    if set(subject.initialization_observation_ids) != expected_initialization_ids:
        raise ValueError(
            "initialization subject must bind the complete governed cohort cut"
        )
    if set(subject.holdout_observation_ids) != expected_holdout_ids:
        raise ValueError("holdout subject must bind the complete governed cohort cut")

    overlap = sorted(expected_initialization_ids & expected_holdout_ids)
    if overlap:
        raise ValueError(
            "governed temporal evidence reuses observation IDs across initialization "
            "and holdout: "
            + ", ".join(overlap)
        )

    return subject
