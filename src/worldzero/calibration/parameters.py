"""Bounded calibration parameter contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParameterBound:
    parameter_id: str
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not self.parameter_id.strip():
            raise ValueError("parameter_id must be non-empty")
        if not math.isfinite(self.lower) or not math.isfinite(self.upper):
            raise ValueError("parameter bounds must be finite")
        if self.lower >= self.upper:
            raise ValueError("lower bound must be less than upper bound")

    @property
    def span(self) -> float:
        return self.upper - self.lower

    def from_unit_interval(self, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("normalized parameter value must be within [0, 1]")
        return self.lower + value * self.span


@dataclass(frozen=True, slots=True)
class ParameterSpace:
    bounds: tuple[ParameterBound, ...]

    def __post_init__(self) -> None:
        if not self.bounds:
            raise ValueError("parameter space requires at least one bound")
        ids = tuple(bound.parameter_id for bound in self.bounds)
        if len(ids) != len(set(ids)):
            raise ValueError("parameter bounds must have unique IDs")

    @property
    def parameter_ids(self) -> tuple[str, ...]:
        return tuple(bound.parameter_id for bound in self.bounds)

    def validate(self, parameters: dict[str, float]) -> None:
        if set(parameters) != set(self.parameter_ids):
            raise ValueError("candidate parameter IDs must exactly match parameter space")
        for bound in self.bounds:
            value = float(parameters[bound.parameter_id])
            if not math.isfinite(value) or not bound.lower <= value <= bound.upper:
                raise ValueError(f"parameter {bound.parameter_id} is outside frozen bounds")
