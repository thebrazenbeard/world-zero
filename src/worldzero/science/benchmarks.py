from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BenchmarkId = Literal["B0_PERSISTENCE_TREND", "B1_REDUCED_FORM_EMPIRICAL"]
BenchmarkStatus = Literal[
    "DRAFT",
    "FROZEN_CANDIDATE",
    "UNDER_TEST",
    "QUALIFIED_WITHIN_SCOPE",
    "REJECTED",
    "SUPERSEDED",
]
BenchmarkMethod = Literal["PERSISTENCE_TREND", "REDUCED_FORM_EMPIRICAL"]


class BenchmarkManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["BENCHMARK_V1"]
    benchmark_id: BenchmarkId
    method_class: BenchmarkMethod
    status: BenchmarkStatus = "DRAFT"
    causal_interpretation: Literal[False] = False
    calibration_only_selection: Literal[True] = True
    final_holdout_access: Literal["FORBIDDEN_UNTIL_FINAL_EVALUATION"] = (
        "FORBIDDEN_UNTIL_FINAL_EVALUATION"
    )
    feature_set_frozen_before_final_holdout: Literal[True] = True
    feature_ids: tuple[str, ...] = ()
    allowed_forms: tuple[str, ...] = ()
    hyperparameter_policy: str | None = None
    regularization_policy: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_benchmark_policy(self) -> BenchmarkManifest:
        if self.benchmark_id == "B0_PERSISTENCE_TREND":
            if self.method_class != "PERSISTENCE_TREND":
                raise ValueError("B0 requires PERSISTENCE_TREND method class")
            if not self.allowed_forms:
                raise ValueError("B0 requires at least one preregistered allowed form")
        elif self.benchmark_id == "B1_REDUCED_FORM_EMPIRICAL":
            if self.method_class != "REDUCED_FORM_EMPIRICAL":
                raise ValueError("B1 requires REDUCED_FORM_EMPIRICAL method class")
            if not self.feature_ids:
                raise ValueError("B1 requires a declared feature set")
            if not self.hyperparameter_policy:
                raise ValueError("B1 requires a calibration-only hyperparameter policy")
            if not self.regularization_policy:
                raise ValueError("B1 requires a regularization policy")
        return self


class BenchmarkRegistry:
    def __init__(self, benchmarks: Iterable[BenchmarkManifest] = ()) -> None:
        self._benchmarks: dict[str, BenchmarkManifest] = {}
        for benchmark in benchmarks:
            if benchmark.benchmark_id in self._benchmarks:
                raise ValueError(f"duplicate benchmark id: {benchmark.benchmark_id}")
            self._benchmarks[benchmark.benchmark_id] = benchmark

    def get(self, benchmark_id: str) -> BenchmarkManifest:
        try:
            return self._benchmarks[benchmark_id]
        except KeyError as exc:
            raise KeyError(f"unknown benchmark id: {benchmark_id}") from exc
