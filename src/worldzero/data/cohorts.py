"""Versioned age-cohort semantics for World Zero V0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from worldzero.sectors.demography import AgeCohort

WPP_V0_AGE_GROUPS = (
    "0-4",
    "5-9",
    "10-14",
    "15-19",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80-84",
    "85-89",
    "90-94",
    "95-99",
    "100+",
)


def _parse_wpp_age_group(label: str) -> tuple[int, int | None]:
    if label == "100+":
        return 100, None
    start_text, end_text = label.split("-", maxsplit=1)
    start = int(start_text)
    end = int(end_text)
    if start < 0 or end < start:
        raise ValueError("invalid WPP age-group interval")
    return start, end


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

        expected_groups = set(WPP_V0_AGE_GROUPS)
        seen_groups: set[str] = set()
        previous_max: int | None = None

        for index, item in enumerate(self.cohorts):
            if item.age_max is None and index != len(self.cohorts) - 1:
                raise ValueError("only the final cohort may be open-ended")
            if index > 0:
                if previous_max is None or item.age_min != previous_max + 1:
                    raise ValueError("cohort ages must be contiguous and non-overlapping")

            item_groups = set(item.source_age_groups)
            if seen_groups & item_groups:
                raise ValueError("source age groups cannot appear in multiple cohorts")

            for source_group in item.source_age_groups:
                if source_group not in expected_groups:
                    raise ValueError("unsupported WPP V0 source age group")
                source_min, source_max = _parse_wpp_age_group(source_group)
                if source_min < item.age_min:
                    raise ValueError("source age group falls outside declared cohort bounds")
                if item.age_max is not None and (
                    source_max is None or source_max > item.age_max
                ):
                    raise ValueError("source age group falls outside declared cohort bounds")

            seen_groups.update(item_groups)
            previous_max = item.age_max

        if self.cohorts[-1].age_max is not None:
            raise ValueError("final cohort must be open-ended")
        if seen_groups != expected_groups:
            raise ValueError("source age groups must exactly cover the frozen WPP V0 age bins")

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
