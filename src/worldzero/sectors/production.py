"""Minimal regional production and capital dynamics."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet
from worldzero.sectors.demography import working_age_population
from worldzero.sectors.energy import (
    EnergyBuildParams,
    dispatch_useful_energy,
    energy_capacity_from_state,
)
from worldzero.sectors.materials import MaterialStockParams, available_material_input_rate


@dataclass(frozen=True, slots=True)
class ProductionParams:
    initial_productive_capital: float
    initial_service_capital: float
    capital_output_ratio: float
    labor_productivity: float
    investment_share: float
    service_investment_fraction: float
    productive_depreciation_rate: float
    service_depreciation_rate: float
    energy_per_output: float | None = None
    material_per_output: float | None = None

    def __post_init__(self) -> None:
        nonnegative = (
            self.initial_productive_capital,
            self.initial_service_capital,
            self.labor_productivity,
            self.productive_depreciation_rate,
            self.service_depreciation_rate,
        )
        if any(value < 0 for value in nonnegative):
            raise ValueError("production parameters must be nonnegative")
        if self.capital_output_ratio <= 0:
            raise ValueError("capital_output_ratio must be positive")
        if not 0 <= self.investment_share <= 1:
            raise ValueError("investment_share must be within [0, 1]")
        if not 0 <= self.service_investment_fraction <= 1:
            raise ValueError("service_investment_fraction must be within [0, 1]")
        for name, value in (
            ("energy_per_output", self.energy_per_output),
            ("material_per_output", self.material_per_output),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when configured")


def productive_capital_stock_id(region_id: str) -> StockId:
    return StockId(f"productive_capital:{region_id}")


def service_capital_stock_id(region_id: str) -> StockId:
    return StockId(f"service_capital:{region_id}")


def region_output(
    state: ModelState,
    region_id: str,
    params: ProductionParams,
    *,
    energy_params: EnergyBuildParams | None = None,
    material_params: MaterialStockParams | None = None,
) -> float:
    capital_capacity = (
        state.value(productive_capital_stock_id(region_id)) / params.capital_output_ratio
    )
    labor_capacity = working_age_population(state, region_id) * params.labor_productivity
    output = min(capital_capacity, labor_capacity)

    if params.energy_per_output is not None:
        if energy_params is None:
            raise ValueError("energy-constrained production requires energy parameters")
        dispatch = dispatch_useful_energy(
            demand=output * params.energy_per_output,
            capacity=energy_capacity_from_state(state, region_id, energy_params),
        )
        output = min(output, dispatch.total_delivered / params.energy_per_output)

    if params.material_per_output is not None:
        if material_params is None:
            raise ValueError("material-constrained production requires material parameters")
        available = available_material_input_rate(state, region_id, material_params)
        output = min(output, available / params.material_per_output)

    return output


def _output_fraction_rate(
    region_id: str,
    params: ProductionParams,
    fraction: float,
    energy_params: EnergyBuildParams | None,
    material_params: MaterialStockParams | None,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return (
            region_output(
                state,
                region_id,
                params,
                energy_params=energy_params,
                material_params=material_params,
            )
            * fraction
        )

    return rate


def _stock_fraction_rate(
    stock_id: StockId, fraction: float
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return fraction * state.value(stock_id)

    return rate


def build_production_sector(
    regions: RegionSet,
    params_by_region: Mapping[str, ProductionParams],
    *,
    energy_params_by_region: Mapping[str, EnergyBuildParams] | None = None,
    material_params_by_region: Mapping[str, MaterialStockParams] | None = None,
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    for region_id in regions.ids:
        params = params_by_region.get(region_id)
        if params is None:
            raise ValueError(f"missing production parameters for {region_id}")
        energy_params = (
            None if energy_params_by_region is None else energy_params_by_region.get(region_id)
        )
        material_params = (
            None if material_params_by_region is None else material_params_by_region.get(region_id)
        )
        if params.energy_per_output is not None and energy_params is None:
            raise ValueError(
                f"missing energy parameters for energy-constrained production in {region_id}"
            )
        if params.material_per_output is not None and material_params is None:
            raise ValueError(
                f"missing material parameters for material-constrained production in {region_id}"
            )
        productive_id = productive_capital_stock_id(region_id)
        service_id = service_capital_stock_id(region_id)
        stocks.extend(
            (
                StockSpec(
                    productive_id,
                    owner="production",
                    unit="capital",
                    initial=params.initial_productive_capital,
                    region=region_id,
                ),
                StockSpec(
                    service_id,
                    owner="production",
                    unit="capital",
                    initial=params.initial_service_capital,
                    region=region_id,
                ),
            )
        )
        productive_fraction = 1.0 - params.service_investment_fraction
        flows.extend(
            (
                FlowSpec(
                    f"productive_investment:{region_id}",
                    source=None,
                    target=productive_id,
                    unit_per_time="capital/year",
                    rate=_output_fraction_rate(
                        region_id,
                        params,
                        params.investment_share * productive_fraction,
                        energy_params,
                        material_params,
                    ),
                ),
                FlowSpec(
                    f"service_investment:{region_id}",
                    source=None,
                    target=service_id,
                    unit_per_time="capital/year",
                    rate=_output_fraction_rate(
                        region_id,
                        params,
                        params.investment_share * params.service_investment_fraction,
                        energy_params,
                        material_params,
                    ),
                ),
            )
        )
        flows.extend(
            (
                FlowSpec(
                    f"productive_depreciation:{region_id}",
                    source=productive_id,
                    target=None,
                    unit_per_time="capital/year",
                    rate=_stock_fraction_rate(productive_id, params.productive_depreciation_rate),
                ),
                FlowSpec(
                    f"service_depreciation:{region_id}",
                    source=service_id,
                    target=None,
                    unit_per_time="capital/year",
                    rate=_stock_fraction_rate(service_id, params.service_depreciation_rate),
                ),
            )
        )
    return tuple(stocks), tuple(flows)
