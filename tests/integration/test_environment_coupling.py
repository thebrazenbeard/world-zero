import pytest

from worldzero.models.environment import ClimateCouplingParams, RegionalEnvironmentParams
from worldzero.models.native_backbone import NativeBackboneConfig, run_native_backbone
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.climate import ClimateParams, ClimateState, LinearDamage
from worldzero.sectors.demography import AgeCohort, DemographyRates
from worldzero.sectors.distribution import DistributionParams
from worldzero.sectors.energy import EnergyBuildParams
from worldzero.sectors.food_land import FoodProductionParams, SoilDynamicsParams
from worldzero.sectors.production import ProductionParams

REGIONS = RegionSet(version="env-test-v1", regions=(RegionDefinition("r1", "R1"),))


def _production(*, energy_per_output: float | None = 1.0) -> ProductionParams:
    return ProductionParams(
        initial_productive_capital=300.0,
        initial_service_capital=0.0,
        capital_output_ratio=3.0,
        labor_productivity=10.0,
        investment_share=0.0,
        service_investment_fraction=0.0,
        productive_depreciation_rate=0.0,
        service_depreciation_rate=0.0,
        energy_per_output=energy_per_output,
    )


def _energy(fossil: float, low: float = 0.0) -> EnergyBuildParams:
    return EnergyBuildParams(
        initial_fossil_capacity=fossil,
        initial_low_carbon_capacity=low,
        initial_grid_capacity=low,
        initial_storage_capacity=0.0,
        initial_cumulative_low_carbon=low,
        annual_low_carbon_build=0.0,
        annual_grid_build=0.0,
        annual_storage_build=0.0,
        fossil_retirement_rate=0.0,
        low_carbon_retirement_rate=0.0,
        low_carbon_capacity_factor=1.0,
    )


def _climate(initial_temperature: float = 0.0) -> ClimateCouplingParams:
    return ClimateCouplingParams(
        initial_state=ClimateState(carbon_burden=0.0, temperature_anomaly=initial_temperature),
        params=ClimateParams(
            airborne_fraction=0.5,
            carbon_decay_rate=0.01,
            carbon_doubling_burden=100.0,
            climate_sensitivity=3.0,
            thermal_response_time=10.0,
        ),
        fossil_emissions_per_useful_energy=1.0,
        output_damage=LinearDamage(slope=0.1, floor=0.4),
    )


def _regional_environment() -> RegionalEnvironmentParams:
    return RegionalEnvironmentParams(
        total_productive_land=100.0,
        bioenergy_land=10.0,
        initial_soil_condition=0.9,
        soil=SoilDynamicsParams(degradation_rate=0.05, recovery_rate=0.02),
        soil_degradation_pressure=1.0,
        soil_restoration_effort=0.0,
        renewable_water_supply=20.0,
        irrigation_demand=40.0,
        other_water_demand=10.0,
        nutrient_input=5.0,
        food_energy_input=5.0,
        food=FoodProductionParams(
            base_yield_per_land=2.0,
            managed_input_gain=1.0,
            water_half_saturation=10.0,
            nutrient_half_saturation=5.0,
            energy_half_saturation=5.0,
        ),
    )


def _config(*, climate=True, regional_environment=True, initial_temperature: float = 0.0):
    return NativeBackboneConfig(
        regions=REGIONS,
        initial_population={"r1": {AgeCohort.YOUNG_ADULT: 100.0}},
        demography_rates={"r1": DemographyRates.zero()},
        migration_links=(),
        production={"r1": _production()},
        distribution={"r1": DistributionParams(labor_share=0.65)},
        start=0.0,
        stop=20.0,
        dt=0.25,
        energy={"r1": _energy(100.0)},
        climate=_climate(initial_temperature) if climate else None,
        environment={"r1": _regional_environment()} if regional_environment else None,
    )


def test_fossil_dispatch_drives_shared_climate_state():
    result = run_native_backbone(_config())
    assert result.climate_state is not None
    assert result.climate_state[-1].carbon_burden > result.climate_state[0].carbon_burden
    assert result.climate_state[-1].temperature_anomaly > 0.0


def test_initial_climate_damage_reduces_real_output():
    damaged = run_native_backbone(_config(initial_temperature=4.0))
    undamaged = run_native_backbone(_config(climate=False, regional_environment=False))
    assert damaged.region_real_output("r1")[0] < undamaged.region_real_output("r1")[0]


def test_soil_degradation_and_water_shortage_reduce_food_access_over_time():
    result = run_native_backbone(_config())
    soil = result.region_soil_condition("r1")
    food = result.region_food_output("r1")
    assert soil[-1] < soil[0]
    assert food[-1] < food[0]
    assert result.region_water_stress("r1")[0] == pytest.approx(2.5)


def test_environment_contracts_fail_closed_when_region_map_is_incomplete():
    two = RegionSet(
        version="env-two",
        regions=(RegionDefinition("r1", "R1"), RegionDefinition("r2", "R2")),
    )
    with pytest.raises(ValueError, match="environment"):
        NativeBackboneConfig(
            regions=two,
            initial_population={
                "r1": {AgeCohort.YOUNG_ADULT: 1.0},
                "r2": {AgeCohort.YOUNG_ADULT: 1.0},
            },
            demography_rates={"r1": DemographyRates.zero(), "r2": DemographyRates.zero()},
            migration_links=(),
            production={"r1": _production(), "r2": _production()},
            distribution={
                "r1": DistributionParams(labor_share=0.6),
                "r2": DistributionParams(labor_share=0.6),
            },
            start=0.0,
            stop=1.0,
            dt=0.25,
            energy={"r1": _energy(10.0), "r2": _energy(10.0)},
            environment={"r1": _regional_environment()},
            climate=None,
        )
