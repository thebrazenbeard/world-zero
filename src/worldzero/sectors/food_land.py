"""Food, land, and soil response functions for native World Zero."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LandAllocation:
    total_productive_land: float
    bioenergy_land: float
    food_land: float


def allocate_land(*, total_productive_land: float, bioenergy_land: float) -> LandAllocation:
    if not math.isfinite(total_productive_land) or total_productive_land < 0:
        raise ValueError("total_productive_land must be finite and nonnegative")
    if not math.isfinite(bioenergy_land) or bioenergy_land < 0:
        raise ValueError("bioenergy_land must be finite and nonnegative")
    if bioenergy_land > total_productive_land:
        raise ValueError("bioenergy land cannot exceed productive land without expansion")
    return LandAllocation(
        total_productive_land=total_productive_land,
        bioenergy_land=bioenergy_land,
        food_land=total_productive_land - bioenergy_land,
    )


@dataclass(frozen=True, slots=True)
class FoodProductionParams:
    base_yield_per_land: float
    managed_input_gain: float
    water_half_saturation: float
    nutrient_half_saturation: float
    energy_half_saturation: float

    def __post_init__(self) -> None:
        if self.base_yield_per_land < 0 or self.managed_input_gain < 0:
            raise ValueError("food yield parameters must be nonnegative")
        if (
            min(
                self.water_half_saturation,
                self.nutrient_half_saturation,
                self.energy_half_saturation,
            )
            <= 0
        ):
            raise ValueError("food input half-saturation constants must be positive")


@dataclass(frozen=True, slots=True)
class FoodProductionResult:
    food_output: float
    water_consumed: float
    nutrient_used: float
    energy_used: float
    managed_input_multiplier: float


def _saturating(input_amount: float, half_saturation: float) -> float:
    if not math.isfinite(input_amount) or input_amount < 0:
        raise ValueError("managed food inputs must be finite and nonnegative")
    return input_amount / (input_amount + half_saturation)


def produce_food(
    *,
    land: LandAllocation,
    soil_condition: float,
    irrigation_water: float,
    nutrient_input: float,
    energy_input: float,
    climate_multiplier: float,
    params: FoodProductionParams,
) -> FoodProductionResult:
    if not 0 <= soil_condition <= 1:
        raise ValueError("soil_condition must be within [0, 1]")
    if not math.isfinite(climate_multiplier) or climate_multiplier < 0:
        raise ValueError("climate_multiplier must be finite and nonnegative")
    water_factor = _saturating(irrigation_water, params.water_half_saturation)
    nutrient_factor = _saturating(nutrient_input, params.nutrient_half_saturation)
    energy_factor = _saturating(energy_input, params.energy_half_saturation)
    managed_factor = (
        1.0 + params.managed_input_gain * (water_factor + nutrient_factor + energy_factor) / 3.0
    )
    output = (
        land.food_land
        * params.base_yield_per_land
        * soil_condition
        * climate_multiplier
        * managed_factor
    )
    return FoodProductionResult(
        food_output=output,
        water_consumed=irrigation_water,
        nutrient_used=nutrient_input,
        energy_used=energy_input,
        managed_input_multiplier=managed_factor,
    )


@dataclass(frozen=True, slots=True)
class SoilDynamicsParams:
    degradation_rate: float
    recovery_rate: float

    def __post_init__(self) -> None:
        if self.degradation_rate < 0 or self.recovery_rate < 0:
            raise ValueError("soil rates must be nonnegative")


def update_soil_condition(
    condition: float,
    *,
    degradation_pressure: float,
    restoration_effort: float,
    dt: float,
    params: SoilDynamicsParams,
) -> float:
    if not 0 <= condition <= 1:
        raise ValueError("soil condition must be within [0, 1]")
    if degradation_pressure < 0 or restoration_effort < 0:
        raise ValueError("soil pressures and efforts must be nonnegative")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")
    degradation = params.degradation_rate * degradation_pressure * condition
    recovery = params.recovery_rate * restoration_effort * (1.0 - condition)
    return min(1.0, max(0.0, condition + dt * (recovery - degradation)))
