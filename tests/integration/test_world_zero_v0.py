from worldzero.models.environment import RegionalEnvironmentParams
from worldzero.models.native_backbone import NativeBackboneConfig
from worldzero.models.world_zero_v0 import WorldZeroV0Config, run_world_zero_v0
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.demography import AgeCohort, DemographyRates
from worldzero.sectors.distribution import DistributionParams
from worldzero.sectors.food_land import FoodProductionParams, SoilDynamicsParams
from worldzero.sectors.institutions import InstitutionParams, PolicyIntervention
from worldzero.sectors.production import ProductionParams
from worldzero.sectors.trade import TradeLink

REGIONS = RegionSet(
    version="v0-test",
    regions=(RegionDefinition("a", "A"), RegionDefinition("b", "B")),
)


def _production() -> ProductionParams:
    return ProductionParams(
        initial_productive_capital=30.0,
        initial_service_capital=0.0,
        capital_output_ratio=3.0,
        labor_productivity=10.0,
        investment_share=0.0,
        service_investment_fraction=0.0,
        productive_depreciation_rate=0.0,
        service_depreciation_rate=0.0,
    )


def _environment(land: float) -> RegionalEnvironmentParams:
    return RegionalEnvironmentParams(
        total_productive_land=land,
        bioenergy_land=0.0,
        initial_soil_condition=1.0,
        soil=SoilDynamicsParams(degradation_rate=0.0, recovery_rate=0.0),
        soil_degradation_pressure=0.0,
        soil_restoration_effort=0.0,
        renewable_water_supply=100.0,
        irrigation_demand=10.0,
        other_water_demand=0.0,
        nutrient_input=1.0,
        food_energy_input=1.0,
        food=FoodProductionParams(
            base_yield_per_land=1.0,
            managed_input_gain=0.0,
            water_half_saturation=1.0,
            nutrient_half_saturation=1.0,
            energy_half_saturation=1.0,
        ),
    )


def _native() -> NativeBackboneConfig:
    return NativeBackboneConfig(
        regions=REGIONS,
        initial_population={
            "a": {AgeCohort.YOUNG_ADULT: 10.0},
            "b": {AgeCohort.YOUNG_ADULT: 10.0},
        },
        demography_rates={"a": DemographyRates.zero(), "b": DemographyRates.zero()},
        migration_links=(),
        production={"a": _production(), "b": _production()},
        distribution={
            "a": DistributionParams(labor_share=0.6),
            "b": DistributionParams(labor_share=0.6),
        },
        start=0.0,
        stop=2.0,
        dt=0.25,
        environment={"a": _environment(100.0), "b": _environment(0.0)},
    )


def test_integrated_v0_moves_food_surplus_and_preserves_policy_delay():
    config = WorldZeroV0Config(
        native=_native(),
        food_requirement_per_person={"a": 5.0, "b": 5.0},
        food_trade_links=(TradeLink("a", "b", capacity=50.0, loss_fraction=0.0),),
        institutions=InstitutionParams(response_capacity=0.5, implementation_delay=1.0),
        intervention=PolicyIntervention(start_time=0.5, magnitude=0.8),
    )
    result = run_world_zero_v0(config)

    assert result.food_trade[0].unmet_demand["b"] == 0.0
    assert result.food_trade[0].mass_balance_difference == 0.0
    before_delay = result.policy[4]  # t=1.0, still before start+delay=1.5
    at_delay = result.policy[6]  # t=1.5
    assert before_delay.effective_magnitude == 0.0
    assert at_delay.effective_magnitude == 0.4
    assert result.native.region_set_version == "v0-test"
