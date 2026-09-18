import pytest

from worldzero.models.native_backbone import NativeBackboneConfig, run_native_backbone
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.demography import AgeCohort, DemographyRates, MigrationLink
from worldzero.sectors.distribution import DistributionParams
from worldzero.sectors.energy import EnergyBuildParams
from worldzero.sectors.materials import MaterialStockParams
from worldzero.sectors.production import ProductionParams

REGIONS = RegionSet(
    version="native-test-v1",
    regions=(RegionDefinition("north", "North"), RegionDefinition("south", "South")),
)


def _production(initial_capital: float) -> ProductionParams:
    return ProductionParams(
        initial_productive_capital=initial_capital,
        initial_service_capital=20.0,
        capital_output_ratio=3.0,
        labor_productivity=4.0,
        investment_share=0.15,
        service_investment_fraction=0.2,
        productive_depreciation_rate=0.04,
        service_depreciation_rate=0.03,
    )


def test_native_backbone_runs_and_preserves_global_population_under_migration_only():
    config = NativeBackboneConfig(
        regions=REGIONS,
        initial_population={
            "north": {AgeCohort.YOUNG_ADULT: 100.0},
            "south": {AgeCohort.YOUNG_ADULT: 50.0},
        },
        demography_rates={
            "north": DemographyRates.zero(),
            "south": DemographyRates.zero(),
        },
        migration_links=(MigrationLink("north", "south", annual_fraction=0.02),),
        production={"north": _production(300.0), "south": _production(180.0)},
        distribution={
            "north": DistributionParams(labor_share=0.65),
            "south": DistributionParams(labor_share=0.7),
        },
        start=0.0,
        stop=5.0,
        dt=0.25,
    )
    result = run_native_backbone(config)

    assert len(result.times) == 21
    assert all(value == pytest.approx(150.0) for value in result.global_population)
    assert result.region_population("north")[-1] < 100.0
    assert result.region_population("south")[-1] > 50.0

    for region_id in REGIONS.ids:
        outputs = result.region_real_output(region_id)
        labor = result.region_labor_income(region_id)
        owners = result.region_owner_income(region_id)
        for output, labor_income, owner_income in zip(outputs, labor, owners, strict=True):
            assert labor_income + owner_income == pytest.approx(output)


def test_native_backbone_result_reports_canonical_region_set_version():
    config = NativeBackboneConfig.minimal(REGIONS)
    result = run_native_backbone(config)
    assert result.region_set_version == "native-test-v1"


def test_native_backbone_config_rejects_missing_region_contracts():
    with pytest.raises(ValueError, match="production"):
        NativeBackboneConfig(
            regions=REGIONS,
            initial_population={"north": {}, "south": {}},
            demography_rates={"north": DemographyRates.zero(), "south": DemographyRates.zero()},
            migration_links=(),
            production={"north": _production(100.0)},
            distribution={
                "north": DistributionParams(labor_share=0.6),
                "south": DistributionParams(labor_share=0.6),
            },
            start=0.0,
            stop=1.0,
            dt=0.25,
        )


def _energy(fossil: float) -> EnergyBuildParams:
    return EnergyBuildParams(
        initial_fossil_capacity=fossil,
        initial_low_carbon_capacity=0.0,
        initial_grid_capacity=0.0,
        initial_storage_capacity=0.0,
        initial_cumulative_low_carbon=0.0,
        annual_low_carbon_build=1.0,
        annual_grid_build=1.0,
        annual_storage_build=0.0,
        fossil_retirement_rate=0.0,
        low_carbon_retirement_rate=0.0,
        low_carbon_capacity_factor=1.0,
    )


def _materials(extraction_fraction: float) -> MaterialStockParams:
    return MaterialStockParams(
        initial_virgin_resource=100.0,
        initial_in_use=20.0,
        initial_waste=0.0,
        initial_lost=0.0,
        extraction_fraction=extraction_fraction,
        processing_yield=1.0,
        retirement_rate=0.0,
        recycling_rate=0.0,
        recycling_yield=0.0,
    )


def test_native_backbone_carries_energy_and_material_stocks_in_same_trajectory():
    config = NativeBackboneConfig(
        regions=REGIONS,
        initial_population={
            "north": {AgeCohort.YOUNG_ADULT: 100.0},
            "south": {AgeCohort.YOUNG_ADULT: 50.0},
        },
        demography_rates={"north": DemographyRates.zero(), "south": DemographyRates.zero()},
        migration_links=(),
        production={"north": _production(300.0), "south": _production(180.0)},
        distribution={
            "north": DistributionParams(labor_share=0.65),
            "south": DistributionParams(labor_share=0.7),
        },
        start=0.0,
        stop=1.0,
        dt=0.25,
        energy={"north": _energy(100.0), "south": _energy(50.0)},
        materials={"north": _materials(0.02), "south": _materials(0.03)},
    )
    result = run_native_backbone(config)
    assert result.region_energy_capacity("north")[
        -1
    ].low_carbon_generation_capacity == pytest.approx(1.0)
    totals = result.region_total_material("north")
    assert all(value == pytest.approx(totals[0], abs=1e-9) for value in totals)


def test_physical_energy_capacity_caps_native_real_output():
    from worldzero.sectors.production import ProductionParams

    production = ProductionParams(
        initial_productive_capital=300.0,
        initial_service_capital=0.0,
        capital_output_ratio=3.0,
        labor_productivity=10.0,
        investment_share=0.0,
        service_investment_fraction=0.0,
        productive_depreciation_rate=0.0,
        service_depreciation_rate=0.0,
        energy_per_output=1.0,
        material_per_output=None,
    )
    one = RegionSet(version="physical-test", regions=(RegionDefinition("r1", "R1"),))
    config = NativeBackboneConfig(
        regions=one,
        initial_population={"r1": {AgeCohort.YOUNG_ADULT: 100.0}},
        demography_rates={"r1": DemographyRates.zero()},
        migration_links=(),
        production={"r1": production},
        distribution={"r1": DistributionParams(labor_share=0.6)},
        start=0.0,
        stop=1.0,
        dt=0.25,
        energy={"r1": _energy(5.0)},
        materials=None,
    )
    result = run_native_backbone(config)
    assert result.region_real_output("r1")[0] == pytest.approx(5.0)


def test_physical_material_throughput_caps_native_real_output():
    production = ProductionParams(
        initial_productive_capital=300.0,
        initial_service_capital=0.0,
        capital_output_ratio=3.0,
        labor_productivity=10.0,
        investment_share=0.0,
        service_investment_fraction=0.0,
        productive_depreciation_rate=0.0,
        service_depreciation_rate=0.0,
        energy_per_output=None,
        material_per_output=1.0,
    )
    one = RegionSet(version="material-cap-test", regions=(RegionDefinition("r1", "R1"),))
    config = NativeBackboneConfig(
        regions=one,
        initial_population={"r1": {AgeCohort.YOUNG_ADULT: 100.0}},
        demography_rates={"r1": DemographyRates.zero()},
        migration_links=(),
        production={"r1": production},
        distribution={"r1": DistributionParams(labor_share=0.6)},
        start=0.0,
        stop=1.0,
        dt=0.25,
        energy=None,
        materials={"r1": _materials(0.01)},
    )
    assert run_native_backbone(config).region_real_output("r1")[0] == pytest.approx(1.0)


def test_declared_energy_intensity_requires_energy_sector():
    production = ProductionParams(
        initial_productive_capital=30.0,
        initial_service_capital=0.0,
        capital_output_ratio=3.0,
        labor_productivity=10.0,
        investment_share=0.0,
        service_investment_fraction=0.0,
        productive_depreciation_rate=0.0,
        service_depreciation_rate=0.0,
        energy_per_output=1.0,
    )
    one = RegionSet(version="fail-closed-test", regions=(RegionDefinition("r1", "R1"),))
    with pytest.raises(ValueError, match="energy sector"):
        NativeBackboneConfig(
            regions=one,
            initial_population={"r1": {AgeCohort.YOUNG_ADULT: 1.0}},
            demography_rates={"r1": DemographyRates.zero()},
            migration_links=(),
            production={"r1": production},
            distribution={"r1": DistributionParams(labor_share=0.6)},
            start=0.0,
            stop=1.0,
            dt=0.25,
        )
