from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

World3Variant = Literal["WORLD3_1974_DYNAMICS", "WORLD3_03_2004"]
World3ReferenceRole = Literal["CANONICAL_F0_CONTROL", "COMPATIBILITY_REFERENCE"]

_EXACT_GITHUB_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
_F0_OBSERVABLES = {
    "POPULATION",
    "INDUSTRIAL_OUTPUT_PER_CAPITA",
    "FOOD_PER_CAPITA",
    "NONRENEWABLE_RESOURCE_FRACTION",
    "PERSISTENT_POLLUTION_INDEX",
}


class World3ReferenceProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD3_REFERENCE_PROFILE_V1"]
    profile_id: str = Field(min_length=1)
    variant: World3Variant
    role: World3ReferenceRole
    start_year: int
    end_year: int
    timestep_years: float = Field(gt=0)
    integration_semantics: Literal["REFERENCE_BACKWARD_EULER_COMPATIBLE"]
    observable_ids: tuple[str, ...]
    primary_references: tuple[str, ...]
    reference_implementations: tuple[str, ...]

    @model_validator(mode="after")
    def validate_profile(self) -> World3ReferenceProfile:
        if self.role == "CANONICAL_F0_CONTROL" and self.variant != "WORLD3_1974_DYNAMICS":
            raise ValueError("canonical F0 control must use WORLD3_1974_DYNAMICS")
        if self.end_year <= self.start_year:
            raise ValueError("end_year must be greater than start_year")
        if set(self.observable_ids) != _F0_OBSERVABLES or len(self.observable_ids) != len(
            _F0_OBSERVABLES
        ):
            raise ValueError(
                "F0 reference observables must match the five comparison observables"
            )
        if not self.primary_references:
            raise ValueError("at least one primary reference is required")
        if not self.reference_implementations:
            raise ValueError("at least one exact reference implementation is required")
        for ref in self.reference_implementations:
            if _EXACT_GITHUB_REF.fullmatch(ref) is None:
                raise ValueError(f"reference implementation must bind an exact commit: {ref}")
        return self


class World3ReferenceRegistry:
    def __init__(self, profiles: Iterable[World3ReferenceProfile] = ()) -> None:
        self._profiles: dict[str, World3ReferenceProfile] = {}
        for profile in profiles:
            if profile.profile_id in self._profiles:
                raise ValueError(f"duplicate World3 reference profile id: {profile.profile_id}")
            self._profiles[profile.profile_id] = profile

    def get(self, profile_id: str) -> World3ReferenceProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"unknown World3 reference profile: {profile_id}") from exc
