"""Versioned age-cohort mappings for World Zero demographic execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from worldzero.sectors.demography import AgeCohort


@dataclass(frozen=True, slots=True)
class AgeCohortBand:
    cohort: AgeCohort
    age_start: int
    age_end: int | None

    def __post_init__(self) -> None:
        if self.age_start < 0:
            raise ValueError("age_start must be nonnegative")
        if self.age_end is not None and self.age_end < self.age_start:
            raise ValueError("age_end must be >= age_start")

    def contains_group(self, age_start: int, age_end: int | None) -> bool:
        if age_start < self.age_start:
            return False
        if self.age_end is None:
            return True
        if age_end is None:
            return False
        return age_end <= self.age_end


@dataclass(frozen=True, slots=True)
class AgeCohortMapping:
    schema_version: str
    mapping_id: str
    status: str
    source_age_scheme: str
    bands: tuple[AgeCohortBand, ...]
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != "AGE_COHORT_MAPPING_V1":
            raise ValueError("unsupported age-cohort mapping schema")
        expected = tuple(AgeCohort)
        actual = tuple(band.cohort for band in self.bands)
        if actual != expected:
            raise ValueError("cohort bands must exactly follow AgeCohort order")
        previous_end = -1
        for index, band in enumerate(self.bands):
            if band.age_start != previous_end + 1:
                raise ValueError("cohort bands must be contiguous")
            if band.age_end is None:
                if index != len(self.bands) - 1:
                    raise ValueError("open-ended cohort must be last")
                break
            previous_end = band.age_end

    def cohort_for_age_group(self, age_start: int, age_end: int | None) -> AgeCohort:
        matches = [
            band.cohort
            for band in self.bands
            if band.contains_group(age_start, age_end)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"age group {age_start}-{age_end} does not map exactly once"
            )
        return matches[0]


def load_age_cohort_mapping(path: Path) -> AgeCohortMapping:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("age-cohort mapping must be a mapping")
    raw_cohorts = payload.get("cohorts")
    if not isinstance(raw_cohorts, list):
        raise TypeError("cohorts must be a list")
    bands = []
    for raw in raw_cohorts:
        if not isinstance(raw, dict):
            raise TypeError("cohort entry must be a mapping")
        bands.append(
            AgeCohortBand(
                cohort=AgeCohort(str(raw["cohort_id"])),
                age_start=int(raw["age_start"]),
                age_end=None if raw.get("age_end") is None else int(raw["age_end"]),
            )
        )
    return AgeCohortMapping(
        schema_version=str(payload["schema_version"]),
        mapping_id=str(payload["mapping_id"]),
        status=str(payload["status"]),
        source_age_scheme=str(payload["source_age_scheme"]),
        bands=tuple(bands),
        notes=None if payload.get("notes") is None else str(payload["notes"]),
    )
