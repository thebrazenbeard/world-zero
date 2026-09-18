"""Runnable native regional demography/production/distribution backbone."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.core import (
    FlowSpec,
    ModelState,
    RK4Solver,
    SimulationClock,
    StockFlowModel,
    StockSpec,
    solve,
)
from worldzero.regions.definitions import RegionSet
from worldzero.sectors.demography import (
    AgeCohort,
    DemographyRates,
    MigrationLink,
    build_demography_sector,
    global_population,
    region_population,
)
from worldzero.sectors.distribution import DistributionParams, allocate_income
from worldzero.sectors.energy import (
    EnergyBuildParams,
    EnergyCapacity,
    build_energy_sector,
    energy_capacity_from_state,
)
from worldzero.sectors.materials import (
    MaterialStockParams,
    build_material_sector,
    total_material_stock,
)
from worldzero.sectors.production import (
    ProductionParams,
    build_production_sector,
    region_output,
)


@dataclass(frozen=True, slots=True)
class NativeBackboneConfig:
    regions: RegionSet
    initial_population: Mapping[str, Mapping[AgeCohort, float]]
    demography_rates: Mapping[str, DemographyRates]
    migration_links: tuple[MigrationLink, ...]
    production: Mapping[str, ProductionParams]
    distribution: Mapping[str, DistributionParams]
    start: float
    stop: float
    dt: float
    energy: Mapping[str, EnergyBuildParams] | None = None
    materials: Mapping[str, MaterialStockParams] | None = None

    def __post_init__(self) -> None:
        expected = set(self.regions.ids)
        for name, mapping in (
            ("initial_population", self.initial_population),
            ("demography_rates", self.demography_rates),
            ("production", self.production),
            ("distribution", self.distribution),
        ):
            actual = set(mapping)
            if actual != expected:
                raise ValueError(f"{name} region keys must exactly match region set")
        if self.energy is not None and set(self.energy) != expected:
            raise ValueError("energy region keys must exactly match region set")
        if self.materials is not None and set(self.materials) != expected:
            raise ValueError("materials region keys must exactly match region set")
        if self.energy is None and any(
            params.energy_per_output is not None for params in self.production.values()
        ):
            raise ValueError("energy-constrained production requires an energy sector")
        if self.materials is None and any(
            params.material_per_output is not None for params in self.production.values()
        ):
            raise ValueError("material-constrained production requires a materials sector")
        SimulationClock(self.start, self.stop, self.dt)

    @classmethod
    def minimal(cls, regions: RegionSet) -> NativeBackboneConfig:
        initial = {region_id: {AgeCohort.YOUNG_ADULT: 1.0} for region_id in regions.ids}
        demography = {region_id: DemographyRates.zero() for region_id in regions.ids}
        production = {
            region_id: ProductionParams(
                initial_productive_capital=3.0,
                initial_service_capital=1.0,
                capital_output_ratio=3.0,
                labor_productivity=10.0,
                investment_share=0.0,
                service_investment_fraction=0.0,
                productive_depreciation_rate=0.0,
                service_depreciation_rate=0.0,
            )
            for region_id in regions.ids
        }
        distribution = {
            region_id: DistributionParams(labor_share=0.65) for region_id in regions.ids
        }
        return cls(
            regions=regions,
            initial_population=initial,
            demography_rates=demography,
            migration_links=(),
            production=production,
            distribution=distribution,
            start=0.0,
            stop=1.0,
            dt=0.25,
        )


@dataclass(frozen=True, slots=True)
class NativeBackboneResult:
    times: tuple[float, ...]
    states: tuple[ModelState, ...]
    regions: RegionSet
    production: Mapping[str, ProductionParams]
    distribution: Mapping[str, DistributionParams]
    energy: Mapping[str, EnergyBuildParams] | None
    materials: Mapping[str, MaterialStockParams] | None

    @property
    def region_set_version(self) -> str:
        return self.regions.version

    @property
    def global_population(self) -> tuple[float, ...]:
        return tuple(global_population(state, self.regions) for state in self.states)

    def region_population(self, region_id: str) -> tuple[float, ...]:
        self.regions.require(region_id)
        return tuple(region_population(state, region_id) for state in self.states)

    def region_real_output(self, region_id: str) -> tuple[float, ...]:
        params = self.production[region_id]
        energy_params = None if self.energy is None else self.energy[region_id]
        material_params = None if self.materials is None else self.materials[region_id]
        return tuple(
            region_output(
                state,
                region_id,
                params,
                energy_params=energy_params,
                material_params=material_params,
            )
            for state in self.states
        )

    def region_energy_capacity(self, region_id: str) -> tuple[EnergyCapacity, ...]:
        if self.energy is None:
            raise ValueError("energy sector is not configured")
        params = self.energy[region_id]
        return tuple(energy_capacity_from_state(state, region_id, params) for state in self.states)

    def region_total_material(self, region_id: str) -> tuple[float, ...]:
        if self.materials is None:
            raise ValueError("materials sector is not configured")
        return tuple(total_material_stock(state, region_id) for state in self.states)

    def region_labor_income(self, region_id: str) -> tuple[float, ...]:
        distribution = self.distribution[region_id]
        return tuple(
            allocate_income(output, distribution).labor_income
            for output in self.region_real_output(region_id)
        )

    def region_owner_income(self, region_id: str) -> tuple[float, ...]:
        distribution = self.distribution[region_id]
        return tuple(
            allocate_income(output, distribution).owner_income
            for output in self.region_real_output(region_id)
        )


def run_native_backbone(config: NativeBackboneConfig) -> NativeBackboneResult:
    demographic_stocks, demographic_flows = build_demography_sector(
        config.regions,
        initial_population=config.initial_population,
        rates_by_region=config.demography_rates,
        migration_links=config.migration_links,
    )
    energy_stocks: tuple[StockSpec, ...] = ()
    energy_flows: tuple[FlowSpec, ...] = ()
    if config.energy is not None:
        energy_stocks, energy_flows = build_energy_sector(config.regions, config.energy)

    material_stocks: tuple[StockSpec, ...] = ()
    material_flows: tuple[FlowSpec, ...] = ()
    if config.materials is not None:
        material_stocks, material_flows = build_material_sector(config.regions, config.materials)

    production_stocks, production_flows = build_production_sector(
        config.regions,
        config.production,
        energy_params_by_region=config.energy,
        material_params_by_region=config.materials,
    )
    model = StockFlowModel(
        stocks=demographic_stocks + production_stocks + energy_stocks + material_stocks,
        flows=demographic_flows + production_flows + energy_flows + material_flows,
    )
    trajectory = solve(
        model,
        SimulationClock(config.start, config.stop, config.dt),
        RK4Solver(),
    )
    return NativeBackboneResult(
        times=trajectory.times,
        states=trajectory.states,
        regions=config.regions,
        production=MappingProxyType(dict(config.production)),
        distribution=MappingProxyType(dict(config.distribution)),
        energy=None if config.energy is None else MappingProxyType(dict(config.energy)),
        materials=None if config.materials is None else MappingProxyType(dict(config.materials)),
    )
