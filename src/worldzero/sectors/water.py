"""Reduced-form renewable-water allocation and stress accounting."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WaterAllocation:
    renewable_supply: float
    irrigation_demand: float
    other_demand: float
    irrigation_delivered: float
    other_delivered: float
    total_delivered: float
    unmet_demand: float
    stress_ratio: float


def allocate_water(
    *,
    renewable_supply: float,
    irrigation_demand: float,
    other_demand: float,
) -> WaterAllocation:
    values = (renewable_supply, irrigation_demand, other_demand)
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("water supply and demand must be finite and nonnegative")
    total_demand = irrigation_demand + other_demand
    if total_demand == 0:
        return WaterAllocation(
            renewable_supply,
            irrigation_demand,
            other_demand,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    ration = min(1.0, renewable_supply / total_demand)
    irrigation_delivered = irrigation_demand * ration
    other_delivered = other_demand * ration
    delivered = irrigation_delivered + other_delivered
    stress = math.inf if renewable_supply == 0 else total_demand / renewable_supply
    return WaterAllocation(
        renewable_supply=renewable_supply,
        irrigation_demand=irrigation_demand,
        other_demand=other_demand,
        irrigation_delivered=irrigation_delivered,
        other_delivered=other_delivered,
        total_delivered=delivered,
        unmet_demand=total_demand - delivered,
        stress_ratio=stress,
    )
