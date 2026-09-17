"""Transparent deployment learning curves."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LearningCurve:
    reference_cost: float
    reference_cumulative_capacity: float
    learning_rate: float
    floor_fraction: float

    def __post_init__(self) -> None:
        if self.reference_cost <= 0:
            raise ValueError("reference_cost must be positive")
        if self.reference_cumulative_capacity <= 0:
            raise ValueError("reference cumulative capacity must be positive")
        if not 0 <= self.learning_rate < 1:
            raise ValueError("learning_rate must be within [0, 1)")
        if not 0 < self.floor_fraction <= 1:
            raise ValueError("floor_fraction must be within (0, 1]")

    def unit_cost(self, cumulative_capacity: float) -> float:
        if not math.isfinite(cumulative_capacity) or cumulative_capacity <= 0:
            raise ValueError("cumulative_capacity must be finite and positive")
        exponent = 0.0 if self.learning_rate == 0 else math.log2(1.0 - self.learning_rate)
        raw = self.reference_cost * (
            cumulative_capacity / self.reference_cumulative_capacity
        ) ** exponent
        return max(self.reference_cost * self.floor_fraction, raw)
