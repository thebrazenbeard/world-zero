"""Reduced-form useful-energy capacity and transparent dispatch."""

from __future__ import annotations

import math
from dataclasses import dataclass


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
    low_generation = (
        capacity.low_carbon_generation_capacity * capacity.low_carbon_capacity_factor
    )
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
