"""Runnable native regional demography/production/distribution backbone."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.core import (
    ModelState,
    RK4Solver,
    SimulationClock,
    StockFlowModel,
    solve,
)
from worldzero.models.environment import (
    ClimateCouplingParams,
    RegionalEnvironmentParams,
    build_environment_sector,
    climate_state_from_model,
    food_output_from_state,
    output_multiplier_from_climate,
    soil_condition_stock_id,
    water_allocation_for_region,
)
from worldzero.models.registry import ModelContribution, ModuleRegistry
from worldzero.regions.definitions import RegionSet
from worldzero.sectors.climate import ClimateState
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
    dispatch_useful_energy,
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


def _output_multiplier_callback(
    climate: ClimateCouplingParams | None,
) -> Callable[[ModelState], float] | None:
    if climate is None:
        return None

    def multiplier(state: ModelState) -> float:
        return output_multiplier_from_climate(state, climate)

    return multiplier


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
    climate: ClimateCouplingParams | None = None
    environment: Mapping[str, RegionalEnvironmentParams] | None = None

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
        if self.environment is not None and set(self.environment) != expected:
            raise ValueError("environment region keys must exactly match region set")
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
    climate: ClimateCouplingParams | None
    environment: Mapping[str, RegionalEnvironmentParams] | None

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
                output_multiplier=output_multiplier_from_climate(state, self.climate),
            )
            for state in self.states
        )

    @property
    def climate_state(self) -> tuple[ClimateState, ...] | None:
        if self.climate is None:
            return None
        return tuple(climate_state_from_model(state) for state in self.states)

    def region_soil_condition(self, region_id: str) -> tuple[float, ...]:
        if self.environment is None:
            raise ValueError("environment sector is not configured")
        return tuple(state.value(soil_condition_stock_id(region_id)) for state in self.states)

    def region_food_output(self, region_id: str) -> tuple[float, ...]:
        if self.environment is None:
            raise ValueError("environment sector is not configured")
        params = self.environment[region_id]
        return tuple(
            food_output_from_state(state, region_id, params, self.climate).food_output
            for state in self.states
        )

    def region_water_stress(self, region_id: str) -> tuple[float, ...]:
        if self.environment is None:
            raise ValueError("environment sector is not configured")
        stress = water_allocation_for_region(self.environment[region_id]).stress_ratio
        return tuple(stress for _ in self.states)

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


def _fossil_emissions_rate(
    config: NativeBackboneConfig,
) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        if config.climate is None or config.energy is None:
            return 0.0
        total = 0.0
        multiplier = output_multiplier_from_climate(state, config.climate)
        for region_id in config.regions.ids:
            production = config.production[region_id]
            if production.energy_per_output is None:
                continue
            energy = config.energy[region_id]
            material = None if config.materials is None else config.materials[region_id]
            output = region_output(
                state,
                region_id,
                production,
                energy_params=energy,
                material_params=material,
                output_multiplier=multiplier,
            )
            dispatch = dispatch_useful_energy(
                demand=output * production.energy_per_output,
                capacity=energy_capacity_from_state(state, region_id, energy),
            )
            total += dispatch.fossil_dispatched * config.climate.fossil_emissions_per_useful_energy
        return total

    return rate


def run_native_backbone(config: NativeBackboneConfig) -> NativeBackboneResult:
    registry = ModuleRegistry()

    demographic_stocks, demographic_flows = build_demography_sector(
        config.regions,
        initial_population=config.initial_population,
        rates_by_region=config.demography_rates,
        migration_links=config.migration_links,
    )
    registry.add(ModelContribution("demography", demographic_stocks, demographic_flows))

    if config.energy is not None:
        stocks, flows = build_energy_sector(config.regions, config.energy)
        registry.add(ModelContribution("energy", stocks, flows))

    if config.materials is not None:
        stocks, flows = build_material_sector(config.regions, config.materials)
        registry.add(ModelContribution("materials", stocks, flows))

    environment_stocks, environment_flows = build_environment_sector(
        config.regions,
        climate=config.climate,
        regional=config.environment,
        emissions_rate=None if config.climate is None else _fossil_emissions_rate(config),
    )
    if environment_stocks or environment_flows:
        registry.add(ModelContribution("environment", environment_stocks, environment_flows))

    production_stocks, production_flows = build_production_sector(
        config.regions,
        config.production,
        energy_params_by_region=config.energy,
        material_params_by_region=config.materials,
        output_multiplier=_output_multiplier_callback(config.climate),
    )
    registry.add(ModelContribution("production", production_stocks, production_flows))

    stocks, flows = registry.compose()
    model = StockFlowModel(stocks=stocks, flows=flows)
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
        climate=config.climate,
        environment=(
            None if config.environment is None else MappingProxyType(dict(config.environment))
        ),
    )
