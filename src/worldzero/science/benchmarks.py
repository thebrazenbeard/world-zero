"""Non-causal predictive benchmark contracts for World Zero."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import content_digest

BenchmarkKind = Literal["B0_PERSISTENCE_TREND", "B1_REDUCED_FORM_EMPIRICAL"]
BenchmarkMethod = Literal[
    "LAST_OBSERVATION_PERSISTENCE",
    "LINEAR_TREND",
    "LOG_LINEAR_TREND",
    "BOUNDED_LOGISTIC_TREND",
    "REGULARIZED_VAR",
    "DYNAMIC_FACTOR",
    "STATE_SPACE",
    "OTHER_FROZEN_REDUCED_FORM",
]


class PredictiveBenchmarkV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["PREDICTIVE_BENCHMARK_V1"]
    benchmark_id: str = Field(min_length=1)
    benchmark_kind: BenchmarkKind
    method: BenchmarkMethod
    observable_ids: tuple[str, ...] = Field(min_length=1)
    calibration_partition_id: str = Field(min_length=1)
    holdout_partition_ids: tuple[str, ...] = Field(min_length=1)
    feature_ids: tuple[str, ...] = ()
    nested_calibration_tuning: bool | None = None
    causal_interpretation: Literal[False] = False
    notes: str | None = None

    @field_validator("observable_ids", "holdout_partition_ids", "feature_ids")
    @classmethod
    def unique_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("benchmark identifier lists must be unique")
        return values

    @model_validator(mode="after")
    def validate_family_rules(self) -> PredictiveBenchmarkV1:
        b0_methods = {
            "LAST_OBSERVATION_PERSISTENCE",
            "LINEAR_TREND",
            "LOG_LINEAR_TREND",
            "BOUNDED_LOGISTIC_TREND",
        }
        if self.benchmark_kind == "B0_PERSISTENCE_TREND":
            if self.method not in b0_methods:
                raise ValueError("B0 benchmark requires a preregistered persistence/trend method")
            if self.feature_ids:
                raise ValueError("B0 benchmark cannot use reduced-form feature_ids")
            return self

        if self.method in b0_methods:
            raise ValueError("B1 benchmark requires a reduced-form empirical method")
        if not self.feature_ids:
            raise ValueError("B1 benchmark requires frozen feature_ids")
        if self.nested_calibration_tuning is not True:
            raise ValueError("B1 hyperparameter selection must be nested inside calibration data")
        return self

    def digest(self) -> str:
        return content_digest(self)

BenchmarkManifest = PredictiveBenchmarkV1
