"""Reduced-form carbon/temperature state and pluggable damage interfaces."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClimateParams:
    airborne_fraction: float
    carbon_decay_rate: float
    carbon_doubling_burden: float
    climate_sensitivity: float
    thermal_response_time: float

    def __post_init__(self) -> None:
        if not 0 <= self.airborne_fraction <= 1:
            raise ValueError("airborne_fraction must be within [0, 1]")
        if self.carbon_decay_rate < 0:
            raise ValueError("carbon_decay_rate must be nonnegative")
        if self.carbon_doubling_burden <= 0:
            raise ValueError("carbon_doubling_burden must be positive")
        if self.climate_sensitivity < 0:
            raise ValueError("climate_sensitivity must be nonnegative")
        if self.thermal_response_time <= 0:
            raise ValueError("thermal_response_time must be positive")


@dataclass(frozen=True, slots=True)
class ClimateState:
    carbon_burden: float
    temperature_anomaly: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.carbon_burden) or self.carbon_burden < 0:
            raise ValueError("carbon_burden must be finite and nonnegative")
        if not math.isfinite(self.temperature_anomaly):
            raise ValueError("temperature_anomaly must be finite")


def _carbon_step(
    carbon: float,
    emissions: float,
    dt: float,
    params: ClimateParams,
) -> float:
    source = params.airborne_fraction * emissions
    decay = params.carbon_decay_rate
    if decay == 0:
        return max(0.0, carbon + source * dt)
    decay_factor = math.exp(-decay * dt)
    equilibrium = source / decay
    return max(0.0, equilibrium + (carbon - equilibrium) * decay_factor)


def step_climate(
    state: ClimateState,
    *,
    emissions: float,
    dt: float,
    params: ClimateParams,
) -> ClimateState:
    if not math.isfinite(emissions):
        raise ValueError("emissions must be finite")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")
    carbon = _carbon_step(state.carbon_burden, emissions, dt, params)
    equilibrium_temperature = params.climate_sensitivity * math.log2(
        1.0 + carbon / params.carbon_doubling_burden
    )
    thermal_factor = math.exp(-dt / params.thermal_response_time)
    temperature = (
        equilibrium_temperature
        + (state.temperature_anomaly - equilibrium_temperature) * thermal_factor
    )
    return ClimateState(carbon_burden=carbon, temperature_anomaly=temperature)


@dataclass(frozen=True, slots=True)
class LinearDamage:
    slope: float
    floor: float = 0.0

    def __post_init__(self) -> None:
        if self.slope < 0:
            raise ValueError("damage slope must be nonnegative")
        if not 0 <= self.floor <= 1:
            raise ValueError("damage floor must be within [0, 1]")

    def multiplier(self, temperature_anomaly: float) -> float:
        temperature = max(0.0, temperature_anomaly)
        return max(self.floor, min(1.0, 1.0 - self.slope * temperature))


@dataclass(frozen=True, slots=True)
class QuadraticDamage:
    linear: float
    quadratic: float
    floor: float = 0.0

    def __post_init__(self) -> None:
        if self.linear < 0 or self.quadratic < 0:
            raise ValueError("damage coefficients must be nonnegative")
        if not 0 <= self.floor <= 1:
            raise ValueError("damage floor must be within [0, 1]")

    def multiplier(self, temperature_anomaly: float) -> float:
        temperature = max(0.0, temperature_anomaly)
        raw = 1.0 - self.linear * temperature - self.quadratic * temperature**2
        return max(self.floor, min(1.0, raw))
