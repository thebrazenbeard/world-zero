"""Integrated V0 scenario runner over the native trajectory and conservative trade/policy layers."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from worldzero.models.native_backbone import (
    NativeBackboneConfig,
    NativeBackboneResult,
    run_native_backbone,
)
from worldzero.sectors.institutions import (
    InstitutionParams,
    PolicyIntervention,
    PolicyResponse,
    policy_response,
)
from worldzero.sectors.trade import PhysicalTradeResult, TradeLink, allocate_physical_trade


@dataclass(frozen=True, slots=True)
class WorldZeroV0Config:
    native: NativeBackboneConfig
    food_requirement_per_person: Mapping[str, float]
    food_trade_links: tuple[TradeLink, ...]
    institutions: InstitutionParams
    intervention: PolicyIntervention | None = None

    def __post_init__(self) -> None:
        expected = set(self.native.regions.ids)
        if set(self.food_requirement_per_person) != expected:
            raise ValueError("food requirement region keys must exactly match region set")
        for value in self.food_requirement_per_person.values():
            if not math.isfinite(value) or value < 0:
                raise ValueError("food requirements must be finite and nonnegative")
        if self.native.environment is None:
            raise ValueError("integrated V0 food-trade scenario requires environment sector")


@dataclass(frozen=True, slots=True)
class WorldZeroV0Result:
    native: NativeBackboneResult
    food_trade: tuple[PhysicalTradeResult, ...]
    policy: tuple[PolicyResponse, ...]


def run_world_zero_v0(config: WorldZeroV0Config) -> WorldZeroV0Result:
    native = run_native_backbone(config.native)
    food_series = {
        region_id: native.region_food_output(region_id) for region_id in config.native.regions.ids
    }
    population_series = {
        region_id: native.region_population(region_id) for region_id in config.native.regions.ids
    }
    trade_results: list[PhysicalTradeResult] = []
    policy_results: list[PolicyResponse] = []

    for index, time in enumerate(native.times):
        supply = {
            region_id: food_series[region_id][index] for region_id in config.native.regions.ids
        }
        demand = {
            region_id: (
                population_series[region_id][index] * config.food_requirement_per_person[region_id]
            )
            for region_id in config.native.regions.ids
        }
        trade_results.append(
            allocate_physical_trade(
                supply_by_region=supply,
                demand_by_region=demand,
                links=config.food_trade_links,
            )
        )
        policy_results.append(policy_response(time, config.institutions, config.intervention))

    return WorldZeroV0Result(
        native=native,
        food_trade=tuple(trade_results),
        policy=tuple(policy_results),
    )
