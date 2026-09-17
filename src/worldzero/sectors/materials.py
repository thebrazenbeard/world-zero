"""Compact material circularity accounting with explicit losses and bottlenecks."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet


@dataclass(frozen=True, slots=True)
class MaterialStepInput:
    beginning_in_use: float
    retirement: float
    virgin_extraction: float
    desired_new_in_use: float
    recycling_rate: float
    recycling_yield: float
    processing_loss_fraction: float

    def __post_init__(self) -> None:
        amounts = (
            self.beginning_in_use,
            self.retirement,
            self.virgin_extraction,
            self.desired_new_in_use,
        )
        if any(not math.isfinite(value) or value < 0 for value in amounts):
            raise ValueError("material amounts must be finite and nonnegative")
        if self.retirement > self.beginning_in_use:
            raise ValueError("retirement cannot exceed material in use")
        for name, value in (
            ("recycling_rate", self.recycling_rate),
            ("recycling_yield", self.recycling_yield),
            ("processing_loss_fraction", self.processing_loss_fraction),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class MaterialStepResult:
    recovered_secondary: float
    recycling_loss: float
    unrecovered_retirement_loss: float
    processing_loss: float
    actual_new_in_use: float
    unused_processed_inventory: float
    unmet_new_in_use: float
    ending_in_use: float
    input_balance_difference: float
    retirement_balance_difference: float


def reconcile_material_step(inputs: MaterialStepInput) -> MaterialStepResult:
    routed_to_recycling = inputs.retirement * inputs.recycling_rate
    recovered = routed_to_recycling * inputs.recycling_yield
    recycling_loss = routed_to_recycling - recovered
    unrecovered_loss = inputs.retirement - routed_to_recycling

    total_input = inputs.virgin_extraction + recovered
    processing_loss = total_input * inputs.processing_loss_fraction
    processed_available = total_input - processing_loss
    actual_new = min(inputs.desired_new_in_use, processed_available)
    unused_inventory = processed_available - actual_new
    unmet = inputs.desired_new_in_use - actual_new
    ending = inputs.beginning_in_use - inputs.retirement + actual_new
    input_difference = total_input - actual_new - processing_loss - unused_inventory
    retirement_difference = inputs.retirement - recovered - recycling_loss - unrecovered_loss
    return MaterialStepResult(
        recovered_secondary=recovered,
        recycling_loss=recycling_loss,
        unrecovered_retirement_loss=unrecovered_loss,
        processing_loss=processing_loss,
        actual_new_in_use=actual_new,
        unused_processed_inventory=unused_inventory,
        unmet_new_in_use=unmet,
        ending_in_use=ending,
        input_balance_difference=input_difference,
        retirement_balance_difference=retirement_difference,
    )


@dataclass(frozen=True, slots=True)
class MaterialStockParams:
    initial_virgin_resource: float
    initial_in_use: float
    initial_waste: float
    initial_lost: float
    extraction_fraction: float
    processing_yield: float
    retirement_rate: float
    recycling_rate: float
    recycling_yield: float

    def __post_init__(self) -> None:
        amounts = (
            self.initial_virgin_resource,
            self.initial_in_use,
            self.initial_waste,
            self.initial_lost,
        )
        if any(not math.isfinite(value) or value < 0 for value in amounts):
            raise ValueError("material stock amounts must be finite and nonnegative")
        for name, value in (
            ("extraction_fraction", self.extraction_fraction),
            ("processing_yield", self.processing_yield),
            ("retirement_rate", self.retirement_rate),
            ("recycling_rate", self.recycling_rate),
            ("recycling_yield", self.recycling_yield),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be within [0, 1]")


def virgin_resource_stock_id(region_id: str) -> StockId:
    return StockId(f"materials:virgin_resource:{region_id}")


def material_in_use_stock_id(region_id: str) -> StockId:
    return StockId(f"materials:in_use:{region_id}")


def material_waste_stock_id(region_id: str) -> StockId:
    return StockId(f"materials:waste:{region_id}")


def material_lost_stock_id(region_id: str) -> StockId:
    return StockId(f"materials:lost:{region_id}")


def _stock_rate(
    stock_id: StockId,
    fraction: float,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return fraction * state.value(stock_id)

    return rate


def build_material_sector(
    regions: RegionSet,
    params_by_region: Mapping[str, MaterialStockParams],
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    for region_id in regions.ids:
        params = params_by_region.get(region_id)
        if params is None:
            raise ValueError(f"missing material parameters for {region_id}")
        virgin_id = virgin_resource_stock_id(region_id)
        use_id = material_in_use_stock_id(region_id)
        waste_id = material_waste_stock_id(region_id)
        lost_id = material_lost_stock_id(region_id)
        stocks.extend(
            (
                StockSpec(
                    virgin_id,
                    owner="materials",
                    unit="material",
                    initial=params.initial_virgin_resource,
                    region=region_id,
                ),
                StockSpec(
                    use_id,
                    owner="materials",
                    unit="material",
                    initial=params.initial_in_use,
                    region=region_id,
                ),
                StockSpec(
                    waste_id,
                    owner="materials",
                    unit="material",
                    initial=params.initial_waste,
                    region=region_id,
                ),
                StockSpec(
                    lost_id,
                    owner="materials",
                    unit="material",
                    initial=params.initial_lost,
                    region=region_id,
                ),
            )
        )
        extraction_good = params.extraction_fraction * params.processing_yield
        extraction_loss = params.extraction_fraction * (1.0 - params.processing_yield)
        recycling_good = params.recycling_rate * params.recycling_yield
        recycling_loss = params.recycling_rate * (1.0 - params.recycling_yield)
        flows.extend(
            (
                FlowSpec(
                    f"materials:virgin_to_use:{region_id}",
                    virgin_id,
                    use_id,
                    "material/year",
                    _stock_rate(virgin_id, extraction_good),
                ),
                FlowSpec(
                    f"materials:virgin_loss:{region_id}",
                    virgin_id,
                    lost_id,
                    "material/year",
                    _stock_rate(virgin_id, extraction_loss),
                ),
                FlowSpec(
                    f"materials:retirement:{region_id}",
                    use_id,
                    waste_id,
                    "material/year",
                    _stock_rate(use_id, params.retirement_rate),
                ),
                FlowSpec(
                    f"materials:recycle_to_use:{region_id}",
                    waste_id,
                    use_id,
                    "material/year",
                    _stock_rate(waste_id, recycling_good),
                ),
                FlowSpec(
                    f"materials:recycling_loss:{region_id}",
                    waste_id,
                    lost_id,
                    "material/year",
                    _stock_rate(waste_id, recycling_loss),
                ),
            )
        )
    return tuple(stocks), tuple(flows)


def total_material_stock(state: ModelState, region_id: str) -> float:
    return sum(
        state.value(stock_id(region_id))
        for stock_id in (
            virgin_resource_stock_id,
            material_in_use_stock_id,
            material_waste_stock_id,
            material_lost_stock_id,
        )
    )
