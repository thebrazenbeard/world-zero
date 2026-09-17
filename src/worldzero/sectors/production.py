"""Minimal regional production and capital dynamics."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet
from worldzero.sectors.demography import working_age_population


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


def productive_capital_stock_id(region_id: str) -> StockId:
    return StockId(f"productive_capital:{region_id}")


def service_capital_stock_id(region_id: str) -> StockId:
    return StockId(f"service_capital:{region_id}")


def region_output(state: ModelState, region_id: str, params: ProductionParams) -> float:
    capital_capacity = state.value(productive_capital_stock_id(region_id)) / params.capital_output_ratio
    labor_capacity = working_age_population(state, region_id) * params.labor_productivity
    return min(capital_capacity, labor_capacity)


def _output_fraction_rate(
    region_id: str, params: ProductionParams, fraction: float
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return region_output(state, region_id, params) * fraction

    return rate


def _stock_fraction_rate(stock_id: StockId, fraction: float) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return fraction * state.value(stock_id)

    return rate


def build_production_sector(
    regions: RegionSet,
    params_by_region: Mapping[str, ProductionParams],
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    for region_id in regions.ids:
        params = params_by_region.get(region_id)
        if params is None:
            raise ValueError(f"missing production parameters for {region_id}")
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
                        region_id, params, params.investment_share * productive_fraction
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
