"""Versioned age-cohort semantics for World Zero V0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from worldzero.sectors.demography import AgeCohort


@dataclass(frozen=True, slots=True)
class AgeCohortDefinition:
    cohort: AgeCohort
    label: str
    age_min: int
    age_max: int | None
    source_age_groups: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("cohort label must be non-empty")
        if self.age_min < 0:
            raise ValueError("cohort age_min must be nonnegative")
        if self.age_max is not None and self.age_max < self.age_min:
            raise ValueError("cohort age_max must be >= age_min")
        if not self.source_age_groups:
            raise ValueError("cohort source_age_groups must be non-empty")


@dataclass(frozen=True, slots=True)
class AgeCohortManifest:
    schema_version: str
    version: str
    status: str
    cohorts: tuple[AgeCohortDefinition, ...]
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != "AGE_COHORT_SET_V1":
            raise ValueError("unsupported age-cohort schema_version")
        if self.status != "FROZEN":
            raise ValueError("age-cohort set must be FROZEN for governed use")
        if tuple(item.cohort for item in self.cohorts) != tuple(AgeCohort):
            raise ValueError("cohort order must exactly match AgeCohort")
        seen_groups: set[str] = set()
        previous_max: int | None = None
        for item in self.cohorts:
            if previous_max is not None and item.age_min != previous_max + 1:
                raise ValueError("cohort ages must be contiguous and non-overlapping")
            if seen_groups & set(item.source_age_groups):
                raise ValueError("source age groups cannot appear in multiple cohorts")
            seen_groups.update(item.source_age_groups)
            previous_max = item.age_max
        if self.cohorts[-1].age_max is not None:
            raise ValueError("final cohort must be open-ended")

    @property
    def source_group_to_cohort(self) -> dict[str, AgeCohort]:
        return {
            age_group: item.cohort
            for item in self.cohorts
            for age_group in item.source_age_groups
        }


def load_age_cohort_manifest(path: Path) -> AgeCohortManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("age-cohort manifest must be a mapping")
    expected = {"schema_version", "version", "status", "cohorts", "notes"}
    if set(payload) != expected:
        raise ValueError("age-cohort manifest fields do not match AGE_COHORT_SET_V1")
    raw_cohorts = payload["cohorts"]
    if not isinstance(raw_cohorts, list):
        raise TypeError("cohorts must be a list")

    cohorts: list[AgeCohortDefinition] = []
    for raw in raw_cohorts:
        if not isinstance(raw, dict):
            raise TypeError("cohort entry must be a mapping")
        cohorts.append(
            AgeCohortDefinition(
                cohort=AgeCohort(str(raw["id"])),
                label=str(raw["label"]),
                age_min=int(raw["age_min"]),
                age_max=None if raw["age_max"] is None else int(raw["age_max"]),
                source_age_groups=tuple(str(item) for item in raw["source_age_groups"]),
            )
        )
    return AgeCohortManifest(
        schema_version=str(payload["schema_version"]),
        version=str(payload["version"]),
        status=str(payload["status"]),
        cohorts=tuple(cohorts),
        notes=None if payload.get("notes") is None else str(payload["notes"]),
    )
