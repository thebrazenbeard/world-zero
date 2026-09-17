import pytest

from worldzero.models.native_backbone import NativeBackboneConfig, run_native_backbone
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.demography import AgeCohort, DemographyRates, MigrationLink
from worldzero.sectors.distribution import DistributionParams
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
