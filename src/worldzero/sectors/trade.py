"""Conservative regional physical-trade allocation with explicit losses and shortages."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.accounting.trade import TradeFlow, reconcile_trade


@dataclass(frozen=True, slots=True)
class TradeLink:
    origin: str
    destination: str
    capacity: float
    loss_fraction: float
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.origin.strip() or not self.destination.strip():
            raise ValueError("trade endpoints must be non-empty")
        if self.origin == self.destination:
            raise ValueError("trade origin and destination must differ")
        if not math.isfinite(self.capacity) or self.capacity < 0:
            raise ValueError("trade capacity must be finite and nonnegative")
        if not 0 <= self.loss_fraction <= 1:
            raise ValueError("trade loss_fraction must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class PhysicalTradeResult:
    flows: tuple[TradeFlow, ...]
    local_consumption: Mapping[str, float]
    delivered_by_trade: Mapping[str, float]
    unmet_demand: Mapping[str, float]
    unused_supply: Mapping[str, float]
    total_losses: float
    trade_reconciliation_difference: float
    mass_balance_difference: float


def _validated_amounts(name: str, values: Mapping[str, float]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for region_id, raw_value in values.items():
        if not region_id.strip():
            raise ValueError(f"{name} region IDs must be non-empty")
        value = float(raw_value)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} values must be finite and nonnegative")
        normalized[region_id] = value
    return normalized


def allocate_physical_trade(
    *,
    supply_by_region: Mapping[str, float],
    demand_by_region: Mapping[str, float],
    links: tuple[TradeLink, ...],
) -> PhysicalTradeResult:
    supply = _validated_amounts("supply", supply_by_region)
    demand = _validated_amounts("demand", demand_by_region)
    regions = tuple(sorted(set(supply) | set(demand)))
    remaining_supply = {region: supply.get(region, 0.0) for region in regions}
    remaining_demand = {region: demand.get(region, 0.0) for region in regions}
    local_consumption: dict[str, float] = {}
    for region in regions:
        consumed = min(remaining_supply[region], remaining_demand[region])
        local_consumption[region] = consumed
        remaining_supply[region] -= consumed
        remaining_demand[region] -= consumed

    flows: list[TradeFlow] = []
    delivered_by_trade: defaultdict[str, float] = defaultdict(float)
    for link in links:
        if link.origin not in remaining_supply or link.destination not in remaining_demand:
            raise ValueError("trade link references a region outside supply/demand maps")
        if not link.enabled or link.capacity == 0 or link.loss_fraction == 1:
            continue
        deliverable_fraction = 1.0 - link.loss_fraction
        shipment = min(
            remaining_supply[link.origin],
            link.capacity,
            remaining_demand[link.destination] / deliverable_fraction,
        )
        if shipment <= 0:
            continue
        loss = shipment * link.loss_fraction
        flow = TradeFlow(
            origin=link.origin,
            destination=link.destination,
            amount=shipment,
            loss=loss,
        )
        flows.append(flow)
        remaining_supply[link.origin] -= shipment
        remaining_demand[link.destination] -= flow.delivered
        delivered_by_trade[link.destination] += flow.delivered

    reconciliation = reconcile_trade(flows)
    total_supply = sum(supply.values())
    accounted = (
        sum(local_consumption.values())
        + sum(delivered_by_trade.values())
        + reconciliation.total_losses
        + sum(remaining_supply.values())
    )
    return PhysicalTradeResult(
        flows=tuple(flows),
        local_consumption=MappingProxyType(local_consumption),
        delivered_by_trade=MappingProxyType(
            {region: delivered_by_trade[region] for region in regions}
        ),
        unmet_demand=MappingProxyType(dict(remaining_demand)),
        unused_supply=MappingProxyType(dict(remaining_supply)),
        total_losses=reconciliation.total_losses,
        trade_reconciliation_difference=reconciliation.difference,
        mass_balance_difference=total_supply - accounted,
    )
