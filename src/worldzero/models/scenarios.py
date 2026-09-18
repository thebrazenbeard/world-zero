"""Typed scenario manifests that separate controls from executable native baselines."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenarioManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_SCENARIO_V1"]
    scenario_id: str = Field(min_length=1)
    scenario_class: Literal["EXTERNAL_CONTROL", "NATIVE_BASELINE"]
    status: Literal["CONTROL_ONLY", "DATA_BINDING_REQUIRED", "EXECUTABLE"]
    start: float
    stop: float
    dt: float
    region_set_version: str | None = None
    data_manifest_id: str | None = None
    parameter_set_id: str | None = None
    reference_artifact: str | None = None
    reference_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    notes: str | None = None

    @model_validator(mode="after")
    def validate_scenario_contract(self) -> ScenarioManifest:
        if self.stop <= self.start:
            raise ValueError("scenario stop must be after start")
        if self.dt <= 0:
            raise ValueError("scenario dt must be positive")
        if self.scenario_class == "EXTERNAL_CONTROL":
            if self.status != "CONTROL_ONLY":
                raise ValueError("external control scenarios must remain CONTROL_ONLY")
            if not self.reference_artifact or not self.reference_sha256:
                raise ValueError("external control requires reference artifact and digest")
        else:
            if not self.region_set_version:
                raise ValueError("native baseline requires region_set_version")
            if self.status == "CONTROL_ONLY":
                raise ValueError("native baseline cannot use CONTROL_ONLY status")
            if self.status == "EXECUTABLE":
                if not self.data_manifest_id:
                    raise ValueError("EXECUTABLE native baseline requires data_manifest_id")
                if not self.parameter_set_id:
                    raise ValueError("EXECUTABLE native baseline requires parameter_set_id")
        return self

    @property
    def executable(self) -> bool:
        return self.status == "EXECUTABLE"


def load_scenario_manifest(path: Path) -> ScenarioManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("scenario manifest must be a mapping")
    return ScenarioManifest.model_validate(payload)
