from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

World3Variant = Literal["WORLD3_1974_DYNAMICS", "WORLD3_03_2004"]
World3ReferenceRole = Literal["CANONICAL_F0_CONTROL", "COMPATIBILITY_REFERENCE"]
World3Scenario = Literal["STANDARD_RUN", "BAU1"]
OracleDelayMethod = Literal["EULER", "IMPLEMENTATION_NATIVE"]
OracleRunMode = Literal["CHECKED_RESCHEDULE", "IMPLEMENTATION_NATIVE"]

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
    scenario_id: World3Scenario
    observable_ids: tuple[str, ...]
    primary_references: tuple[str, ...]

    @model_validator(mode="after")
    def validate_profile(self) -> World3ReferenceProfile:
        if self.role == "CANONICAL_F0_CONTROL":
            if self.variant != "WORLD3_1974_DYNAMICS":
                raise ValueError(
                    "canonical F0 control must use WORLD3_1974_DYNAMICS"
                )
            if self.scenario_id != "STANDARD_RUN":
                raise ValueError("canonical F0 control must use STANDARD_RUN")
        if set(self.observable_ids) != _F0_OBSERVABLES or len(
            self.observable_ids
        ) != len(_F0_OBSERVABLES):
            raise ValueError(
                "F0 reference observables must match the five comparison observables"
            )
        if not self.primary_references:
            raise ValueError("at least one primary reference is required")
        return self


class World3ObservableBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observable_id: str = Field(min_length=1)
    implementation_name: str = Field(min_length=1)


class World3OracleExecutionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD3_ORACLE_EXECUTION_V1"]
    oracle_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    implementation_ref: str
    start_year: int
    end_year: int
    timestep_years: float = Field(gt=0)
    endpoint_inclusive: bool
    sample_count: int = Field(gt=1)
    delay_method: OracleDelayMethod
    run_mode: OracleRunMode
    constants_mode: Literal["IMPLEMENTATION_DEFAULTS"]
    tables_mode: Literal["IMPLEMENTATION_DEFAULTS"]
    initialization_sequence: tuple[str, ...]
    observable_bindings: tuple[World3ObservableBinding, ...]

    @model_validator(mode="after")
    def validate_execution(self) -> World3OracleExecutionSpec:
        if _EXACT_GITHUB_REF.fullmatch(self.implementation_ref) is None:
            raise ValueError("implementation_ref must bind an exact GitHub commit")
        if self.end_year <= self.start_year:
            raise ValueError("end_year must be greater than start_year")
        intervals = (self.end_year - self.start_year) / self.timestep_years
        if not intervals.is_integer():
            raise ValueError("time span must be an integer number of timesteps")
        expected = int(intervals) + (1 if self.endpoint_inclusive else 0)
        if self.sample_count != expected:
            raise ValueError(
                f"sample_count must be {expected} for the declared time grid"
            )
        binding_ids = [binding.observable_id for binding in self.observable_bindings]
        if len(binding_ids) != len(set(binding_ids)):
            raise ValueError("oracle observable bindings contain duplicate ids")
        if set(binding_ids) != _F0_OBSERVABLES:
            raise ValueError(
                "oracle bindings must cover exactly the five F0 observables"
            )
        if not self.initialization_sequence:
            raise ValueError("oracle initialization_sequence is required")
        return self


class World3ReferenceRegistry:
    def __init__(self, profiles: Iterable[World3ReferenceProfile] = ()) -> None:
        self._profiles: dict[str, World3ReferenceProfile] = {}
        for profile in profiles:
            if profile.profile_id in self._profiles:
                raise ValueError(
                    f"duplicate World3 reference profile id: {profile.profile_id}"
                )
            self._profiles[profile.profile_id] = profile

    def get(self, profile_id: str) -> World3ReferenceProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown World3 reference profile: {profile_id}"
            ) from exc
