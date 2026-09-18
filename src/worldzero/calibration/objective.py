"""Calibration objective bound strictly to the frozen calibration partition."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.science.partitions import PartitionSet


@dataclass(frozen=True, slots=True)
class ObjectiveTerm:
    observation_id: str
    observed: float
    scale: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        if not math.isfinite(self.observed):
            raise ValueError("observed value must be finite")
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise ValueError("objective scale must be finite and positive")
        if not math.isfinite(self.weight) or self.weight <= 0:
            raise ValueError("objective weight must be finite and positive")


@dataclass(frozen=True, slots=True)
class CalibrationObjectiveResult:
    term_ids: tuple[str, ...]
    normalized_residuals: Mapping[str, float]
    weighted_squared_error: float


@dataclass(frozen=True, slots=True)
class CalibrationObjective:
    partition_set: PartitionSet
    terms: tuple[ObjectiveTerm, ...]

    def __post_init__(self) -> None:
        if not self.terms:
            raise ValueError("calibration objective requires at least one term")
        ids = tuple(term.observation_id for term in self.terms)
        if len(ids) != len(set(ids)):
            raise ValueError("calibration objective observation IDs must be unique")
        holdouts = self.partition_set.final_holdout_ids
        leaked = sorted(set(ids) & holdouts)
        if leaked:
            raise ValueError(
                "holdout observation(s) in calibration objective: " + ", ".join(leaked)
            )
        unknown = sorted(set(ids) - self.partition_set.calibration_ids)
        if unknown:
            raise ValueError(
                "objective observation(s) are not in frozen calibration partition: "
                + ", ".join(unknown)
            )

    def evaluate(self, predictions: Mapping[str, float]) -> CalibrationObjectiveResult:
        residuals: dict[str, float] = {}
        weighted_squared_error = 0.0
        for term in self.terms:
            if term.observation_id not in predictions:
                raise KeyError(f"missing prediction for {term.observation_id}")
            prediction = float(predictions[term.observation_id])
            if not math.isfinite(prediction):
                raise ValueError(f"prediction for {term.observation_id} must be finite")
            residual = (prediction - term.observed) / term.scale
            residuals[term.observation_id] = residual
            weighted_squared_error += term.weight * residual**2
        return CalibrationObjectiveResult(
            term_ids=tuple(term.observation_id for term in self.terms),
            normalized_residuals=MappingProxyType(residuals),
            weighted_squared_error=weighted_squared_error,
        )
