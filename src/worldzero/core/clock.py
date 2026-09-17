"""Deterministic simulation clock."""

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationClock:
    start: float
    stop: float
    dt: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.start, self.stop, self.dt)):
            raise ValueError("clock values must be finite")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.stop < self.start:
            raise ValueError("stop must be greater than or equal to start")
        steps = (self.stop - self.start) / self.dt
        if not math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("clock horizon must be an integer number of timesteps")

    @property
    def step_count(self) -> int:
        return round((self.stop - self.start) / self.dt)

    def times(self) -> tuple[float, ...]:
        return tuple(self.start + i * self.dt for i in range(self.step_count + 1))
