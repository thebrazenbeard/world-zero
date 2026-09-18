"""Environmental coupling primitives owned by the model layer."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet
from worldzero.sectors.climate import ClimateParams, ClimateState
from worldzero.sectors.food_land import (
    FoodProductionParams,
    FoodProductionResult,
    SoilDynamicsParams,
    allocate_land,
    produce_food,
)
from worldzero.sectors.water import WaterAllocation, allocate_water


class DamageFunction(Protocol):
    def multiplier(self, temperature_anomaly: float) -> float: ...


@dataclass(frozen=True, slots=True)
class ClimateCouplingParams:
    initial_state: ClimateState
    params: ClimateParams
    fossil_emissions_per_useful_energy: float
    output_damage: DamageFunction

    def __post_init__(self) -> None:
        factor = self.fossil_emissions_per_useful_energy
        if not math.isfinite(factor) or factor < 0:
            raise ValueError("fossil emissions factor must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class RegionalEnvironmentParams:
    total_productive_land: float
    bioenergy_land: float
    initial_soil_condition: float
    soil: SoilDynamicsParams
    soil_degradation_pressure: float
    soil_restoration_effort: float
    renewable_water_supply: float
    irrigation_demand: float
    other_water_demand: float
    nutrient_input: float
    food_energy_input: float
    food: FoodProductionParams

    def __post_init__(self) -> None:
        allocate_land(
            total_productive_land=self.total_productive_land,
            bioenergy_land=self.bioenergy_land,
        )
        allocate_water(
            renewable_supply=self.renewable_water_supply,
            irrigation_demand=self.irrigation_demand,
            other_demand=self.other_water_demand,
        )
        if not 0 <= self.initial_soil_condition <= 1:
            raise ValueError("initial_soil_condition must be within [0, 1]")
        if self.soil_degradation_pressure < 0 or self.soil_restoration_effort < 0:
            raise ValueError("soil pressure and restoration effort must be nonnegative")
        if self.nutrient_input < 0 or self.food_energy_input < 0:
            raise ValueError("food nutrient and energy inputs must be nonnegative")


def climate_carbon_stock_id() -> StockId:
    return StockId("climate:carbon_burden")


def climate_temperature_stock_id() -> StockId:
    return StockId("climate:temperature_anomaly")


def soil_condition_stock_id(region_id: str) -> StockId:
    return StockId(f"environment:soil_condition:{region_id}")


def climate_state_from_model(state: ModelState) -> ClimateState:
    return ClimateState(
        carbon_burden=state.value(climate_carbon_stock_id()),
        temperature_anomaly=state.value(climate_temperature_stock_id()),
    )


def output_multiplier_from_climate(
    state: ModelState,
    climate: ClimateCouplingParams | None,
) -> float:
    if climate is None:
        return 1.0
    temperature = state.value(climate_temperature_stock_id())
    multiplier = float(climate.output_damage.multiplier(temperature))
    if not 0 <= multiplier <= 1:
        raise ValueError("climate damage multiplier must be within [0, 1]")
    return multiplier


def _carbon_decay_rate(
    climate: ClimateCouplingParams,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return climate.params.carbon_decay_rate * state.value(climate_carbon_stock_id())

    return rate


def _emissions_inflow_rate(
    climate: ClimateCouplingParams,
    emissions_rate: Callable[[ModelState, float], float],
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, t: float) -> float:
        emissions = float(emissions_rate(state, t))
        if not math.isfinite(emissions) or emissions < 0:
            raise ValueError("fossil emissions rate must be finite and nonnegative")
        return climate.params.airborne_fraction * emissions

    return rate


def _temperature_target(state: ModelState, climate: ClimateCouplingParams) -> float:
    carbon = state.value(climate_carbon_stock_id())
    return climate.params.climate_sensitivity * math.log2(
        1.0 + carbon / climate.params.carbon_doubling_burden
    )


def _temperature_warming_rate(
    climate: ClimateCouplingParams,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        current = state.value(climate_temperature_stock_id())
        target = _temperature_target(state, climate)
        return max(0.0, target - current) / climate.params.thermal_response_time

    return rate


def _temperature_cooling_rate(
    climate: ClimateCouplingParams,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        current = state.value(climate_temperature_stock_id())
        target = _temperature_target(state, climate)
        return max(0.0, current - target) / climate.params.thermal_response_time

    return rate


def _soil_degradation_rate(
    stock_id: StockId,
    params: RegionalEnvironmentParams,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        condition = state.value(stock_id)
        return params.soil.degradation_rate * params.soil_degradation_pressure * condition

    return rate


def _soil_recovery_rate(
    stock_id: StockId,
    params: RegionalEnvironmentParams,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        condition = state.value(stock_id)
        return (
            params.soil.recovery_rate * params.soil_restoration_effort * max(0.0, 1.0 - condition)
        )

    return rate


def build_environment_sector(
    regions: RegionSet,
    *,
    climate: ClimateCouplingParams | None,
    regional: Mapping[str, RegionalEnvironmentParams] | None,
    emissions_rate: Callable[[ModelState, float], float] | None,
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    if climate is not None:
        if emissions_rate is None:
            raise ValueError("climate coupling requires an emissions-rate function")
        carbon_id = climate_carbon_stock_id()
        temperature_id = climate_temperature_stock_id()
        stocks.extend(
            (
                StockSpec(
                    carbon_id,
                    owner="climate",
                    unit="carbon",
                    initial=climate.initial_state.carbon_burden,
                ),
                StockSpec(
                    temperature_id,
                    owner="climate",
                    unit="temperature",
                    initial=climate.initial_state.temperature_anomaly,
                    nonnegative=False,
                ),
            )
        )
        flows.extend(
            (
                FlowSpec(
                    "climate:emissions",
                    source=None,
                    target=carbon_id,
                    unit_per_time="carbon/year",
                    rate=_emissions_inflow_rate(climate, emissions_rate),
                ),
                FlowSpec(
                    "climate:carbon_decay",
                    source=carbon_id,
                    target=None,
                    unit_per_time="carbon/year",
                    rate=_carbon_decay_rate(climate),
                ),
                FlowSpec(
                    "climate:warming",
                    source=None,
                    target=temperature_id,
                    unit_per_time="temperature/year",
                    rate=_temperature_warming_rate(climate),
                ),
                FlowSpec(
                    "climate:cooling",
                    source=temperature_id,
                    target=None,
                    unit_per_time="temperature/year",
                    rate=_temperature_cooling_rate(climate),
                ),
            )
        )
    if regional is not None:
        for region_id in regions.ids:
            params = regional.get(region_id)
            if params is None:
                raise ValueError(f"missing environment parameters for {region_id}")
            soil_id = soil_condition_stock_id(region_id)
            stocks.append(
                StockSpec(
                    soil_id,
                    owner="environment",
                    unit="condition",
                    initial=params.initial_soil_condition,
                    region=region_id,
                )
            )
            flows.extend(
                (
                    FlowSpec(
                        f"environment:soil_recovery:{region_id}",
                        source=None,
                        target=soil_id,
                        unit_per_time="condition/year",
                        rate=_soil_recovery_rate(soil_id, params),
                    ),
                    FlowSpec(
                        f"environment:soil_degradation:{region_id}",
                        source=soil_id,
                        target=None,
                        unit_per_time="condition/year",
                        rate=_soil_degradation_rate(soil_id, params),
                    ),
                )
            )
    return tuple(stocks), tuple(flows)


def water_allocation_for_region(params: RegionalEnvironmentParams) -> WaterAllocation:
    return allocate_water(
        renewable_supply=params.renewable_water_supply,
        irrigation_demand=params.irrigation_demand,
        other_demand=params.other_water_demand,
    )


def food_output_from_state(
    state: ModelState,
    region_id: str,
    params: RegionalEnvironmentParams,
    climate: ClimateCouplingParams | None,
) -> FoodProductionResult:
    water = water_allocation_for_region(params)
    land = allocate_land(
        total_productive_land=params.total_productive_land,
        bioenergy_land=params.bioenergy_land,
    )
    climate_multiplier = output_multiplier_from_climate(state, climate)
    return produce_food(
        land=land,
        soil_condition=state.value(soil_condition_stock_id(region_id)),
        irrigation_water=water.irrigation_delivered,
        nutrient_input=params.nutrient_input,
        energy_input=params.food_energy_input,
        climate_multiplier=climate_multiplier,
        params=params.food,
    )
