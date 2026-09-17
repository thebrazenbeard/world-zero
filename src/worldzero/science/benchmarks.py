"""Non-causal predictive benchmark manifests and leakage guards."""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Set as AbstractSet
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

BenchmarkId = Literal["B0_PERSISTENCE_TREND", "B1_REDUCED_FORM_EMPIRICAL"]
BenchmarkMethod = Literal[
    "PERSISTENCE",
    "LINEAR_TREND",
    "LOG_LINEAR_TREND",
    "BOUNDED_LOGISTIC_TREND",
    "REGULARIZED_VAR",
    "DYNAMIC_FACTOR",
    "STATE_SPACE",
    "OTHER_PREREGISTERED_REDUCED_FORM",
]


class BenchmarkManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    benchmark_id: BenchmarkId
    method: BenchmarkMethod
    causal_interpretation: Literal[False] = False
    feature_set: tuple[str, ...] = ()
    allowed_forms: tuple[str, ...] = ()
    regularization_policy: str | None = None
    hyperparameter_policy: str | None = None
    transformation_policy: str | None = None
    partition_binding_required: bool = True
    notes: str | None = None

    @model_validator(mode="after")
    def validate_benchmark_contract(self) -> BenchmarkManifest:
        if self.benchmark_id == "B0_PERSISTENCE_TREND":
            if self.method not in {
                "PERSISTENCE",
                "LINEAR_TREND",
                "LOG_LINEAR_TREND",
                "BOUNDED_LOGISTIC_TREND",
            }:
                raise ValueError("B0 method must be a preregistered persistence/trend form")
        else:
            if self.method not in {
                "REGULARIZED_VAR",
                "DYNAMIC_FACTOR",
                "STATE_SPACE",
                "OTHER_PREREGISTERED_REDUCED_FORM",
            }:
                raise ValueError("B1 method must be a reduced-form empirical method")
            if not self.feature_set:
                raise ValueError("B1 feature_set must be frozen before final holdout evaluation")
            if not self.hyperparameter_policy:
                raise ValueError("B1 hyperparameter_policy must be declared")
            if self.method == "REGULARIZED_VAR" and not self.regularization_policy:
                raise ValueError("REGULARIZED_VAR requires regularization_policy")
        return self


class BenchmarkRegistry:
    def __init__(self, manifests: Iterable[BenchmarkManifest] = ()) -> None:
        self._by_id: dict[str, BenchmarkManifest] = {}
        for manifest in manifests:
            if manifest.benchmark_id in self._by_id:
                raise ValueError(f"duplicate benchmark_id: {manifest.benchmark_id}")
            self._by_id[manifest.benchmark_id] = manifest

    def get(self, benchmark_id: str) -> BenchmarkManifest:
        try:
            return self._by_id[benchmark_id]
        except KeyError as exc:
            raise KeyError(f"unknown benchmark_id: {benchmark_id}") from exc


def calibration_only_observation_ids(
    calibration_ids: AbstractSet[str] | set[str], final_holdout_ids: AbstractSet[str] | set[str]
) -> set[str]:
    """Return calibration IDs for tuning, failing closed on final-holdout leakage."""
    overlap = sorted(set(calibration_ids) & set(final_holdout_ids))
    if overlap:
        raise ValueError("calibration/final-holdout overlap: " + ", ".join(overlap))
    return set(calibration_ids)
