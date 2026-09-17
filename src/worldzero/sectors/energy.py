"""Reduced-form useful-energy capacity and transparent dispatch."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet


@dataclass(frozen=True, slots=True)
class EnergyCapacity:
    fossil_useful_capacity: float
    low_carbon_generation_capacity: float
    low_carbon_capacity_factor: float
    grid_delivery_capacity: float
    storage_power_capacity: float

    def __post_init__(self) -> None:
        capacities = (
            self.fossil_useful_capacity,
            self.low_carbon_generation_capacity,
            self.grid_delivery_capacity,
            self.storage_power_capacity,
        )
        if any(not math.isfinite(value) or value < 0 for value in capacities):
            raise ValueError("energy capacities must be finite and nonnegative")
        if not 0 <= self.low_carbon_capacity_factor <= 1:
            raise ValueError("low_carbon_capacity_factor must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class EnergyDispatch:
    demand: float
    low_carbon_available: float
    low_carbon_dispatched: float
    fossil_dispatched: float
    total_delivered: float
    unserved_demand: float


def dispatch_useful_energy(*, demand: float, capacity: EnergyCapacity) -> EnergyDispatch:
    if not math.isfinite(demand) or demand < 0:
        raise ValueError("energy demand must be finite and nonnegative")
    low_generation = capacity.low_carbon_generation_capacity * capacity.low_carbon_capacity_factor
    low_available = min(low_generation, capacity.grid_delivery_capacity)
    low_dispatched = min(demand, low_available)
    remaining = demand - low_dispatched
    fossil_dispatched = min(remaining, capacity.fossil_useful_capacity)
    delivered = low_dispatched + fossil_dispatched
    return EnergyDispatch(
        demand=demand,
        low_carbon_available=low_available,
        low_carbon_dispatched=low_dispatched,
        fossil_dispatched=fossil_dispatched,
        total_delivered=delivered,
        unserved_demand=demand - delivered,
    )


@dataclass(frozen=True, slots=True)
class EnergyBuildParams:
    initial_fossil_capacity: float
    initial_low_carbon_capacity: float
    initial_grid_capacity: float
    initial_storage_capacity: float
    initial_cumulative_low_carbon: float
    annual_low_carbon_build: float
    annual_grid_build: float
    annual_storage_build: float
    fossil_retirement_rate: float
    low_carbon_retirement_rate: float
    low_carbon_capacity_factor: float

    def __post_init__(self) -> None:
        amounts = (
            self.initial_fossil_capacity,
            self.initial_low_carbon_capacity,
            self.initial_grid_capacity,
            self.initial_storage_capacity,
            self.initial_cumulative_low_carbon,
            self.annual_low_carbon_build,
            self.annual_grid_build,
            self.annual_storage_build,
        )
        if any(not math.isfinite(value) or value < 0 for value in amounts):
            raise ValueError("energy build parameters must be finite and nonnegative")
        if self.initial_cumulative_low_carbon < self.initial_low_carbon_capacity:
            raise ValueError("cumulative low-carbon deployment cannot be below installed capacity")
        if not 0 <= self.fossil_retirement_rate <= 1:
            raise ValueError("fossil_retirement_rate must be within [0, 1]")
        if not 0 <= self.low_carbon_retirement_rate <= 1:
            raise ValueError("low_carbon_retirement_rate must be within [0, 1]")
        if not 0 <= self.low_carbon_capacity_factor <= 1:
            raise ValueError("low_carbon_capacity_factor must be within [0, 1]")


def fossil_capacity_stock_id(region_id: str) -> StockId:
    return StockId(f"energy:fossil_capacity:{region_id}")


def low_carbon_capacity_stock_id(region_id: str) -> StockId:
    return StockId(f"energy:low_carbon_capacity:{region_id}")


def grid_capacity_stock_id(region_id: str) -> StockId:
    return StockId(f"energy:grid_capacity:{region_id}")


def storage_capacity_stock_id(region_id: str) -> StockId:
    return StockId(f"energy:storage_capacity:{region_id}")


def cumulative_low_carbon_stock_id(region_id: str) -> StockId:
    return StockId(f"energy:cumulative_low_carbon:{region_id}")


def _constant_rate(value: float) -> Callable[[ModelState, float], float]:
    def rate(_state: ModelState, _t: float) -> float:
        return value

    return rate


def _fractional_rate(stock_id: StockId, fraction: float) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return fraction * state.value(stock_id)

    return rate


def build_energy_sector(
    regions: RegionSet,
    params_by_region: Mapping[str, EnergyBuildParams],
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    for region_id in regions.ids:
        params = params_by_region.get(region_id)
        if params is None:
            raise ValueError(f"missing energy parameters for {region_id}")
        fossil_id = fossil_capacity_stock_id(region_id)
        low_id = low_carbon_capacity_stock_id(region_id)
        grid_id = grid_capacity_stock_id(region_id)
        storage_id = storage_capacity_stock_id(region_id)
        cumulative_id = cumulative_low_carbon_stock_id(region_id)
        stocks.extend(
            (
                StockSpec(
                    fossil_id,
                    owner="energy",
                    unit="capacity",
                    initial=params.initial_fossil_capacity,
                    region=region_id,
                ),
                StockSpec(
                    low_id,
                    owner="energy",
                    unit="capacity",
                    initial=params.initial_low_carbon_capacity,
                    region=region_id,
                ),
                StockSpec(
                    grid_id,
                    owner="energy",
                    unit="capacity",
                    initial=params.initial_grid_capacity,
                    region=region_id,
                ),
                StockSpec(
                    storage_id,
                    owner="energy",
                    unit="capacity",
                    initial=params.initial_storage_capacity,
                    region=region_id,
                ),
                StockSpec(
                    cumulative_id,
                    owner="energy",
                    unit="capacity",
                    initial=params.initial_cumulative_low_carbon,
                    region=region_id,
                ),
            )
        )
        flows.extend(
            (
                FlowSpec(
                    f"energy:low_build:{region_id}",
                    None,
                    low_id,
                    "capacity/year",
                    _constant_rate(params.annual_low_carbon_build),
                ),
                FlowSpec(
                    f"energy:low_cumulative:{region_id}",
                    None,
                    cumulative_id,
                    "capacity/year",
                    _constant_rate(params.annual_low_carbon_build),
                ),
                FlowSpec(
                    f"energy:grid_build:{region_id}",
                    None,
                    grid_id,
                    "capacity/year",
                    _constant_rate(params.annual_grid_build),
                ),
                FlowSpec(
                    f"energy:storage_build:{region_id}",
                    None,
                    storage_id,
                    "capacity/year",
                    _constant_rate(params.annual_storage_build),
                ),
                FlowSpec(
                    f"energy:fossil_retire:{region_id}",
                    fossil_id,
                    None,
                    "capacity/year",
                    _fractional_rate(fossil_id, params.fossil_retirement_rate),
                ),
                FlowSpec(
                    f"energy:low_retire:{region_id}",
                    low_id,
                    None,
                    "capacity/year",
                    _fractional_rate(low_id, params.low_carbon_retirement_rate),
                ),
            )
        )
    return tuple(stocks), tuple(flows)


def energy_capacity_from_state(
    state: ModelState,
    region_id: str,
    params: EnergyBuildParams,
) -> EnergyCapacity:
    return EnergyCapacity(
        fossil_useful_capacity=state.value(fossil_capacity_stock_id(region_id)),
        low_carbon_generation_capacity=state.value(low_carbon_capacity_stock_id(region_id)),
        low_carbon_capacity_factor=params.low_carbon_capacity_factor,
        grid_delivery_capacity=state.value(grid_capacity_stock_id(region_id)),
        storage_power_capacity=state.value(storage_capacity_stock_id(region_id)),
    )
