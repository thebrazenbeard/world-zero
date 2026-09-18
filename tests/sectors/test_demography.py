import pytest

from worldzero.core import EulerSolver, SimulationClock, StockFlowModel, solve
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.demography import (
    AgeCohort,
    DemographyRates,
    MigrationLink,
    build_demography_sector,
    global_population,
    region_population,
)

REGIONS = RegionSet(
    version="test-v1",
    regions=(RegionDefinition("north", "North"), RegionDefinition("south", "South")),
)


def _initial(north: float = 100.0, south: float = 0.0):
    return {
        "north": {AgeCohort.YOUNG_ADULT: north},
        "south": {AgeCohort.YOUNG_ADULT: south},
    }


def test_zero_demography_rates_hold_population_constant():
    stocks, flows = build_demography_sector(
        REGIONS,
        initial_population=_initial(100.0, 50.0),
        rates_by_region={"north": DemographyRates.zero(), "south": DemographyRates.zero()},
    )
    trajectory = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 5.0, 0.25),
        EulerSolver(),
    )
    assert all(global_population(state, REGIONS) == pytest.approx(150.0) for state in trajectory.states)


def test_ageing_moves_people_between_cohorts_without_creating_people():
    rates = DemographyRates.zero(ageing={AgeCohort.CHILD: 0.1})
    initial = {
        "north": {AgeCohort.CHILD: 100.0},
        "south": {},
    }
    stocks, flows = build_demography_sector(
        REGIONS,
        initial_population=initial,
        rates_by_region={"north": rates, "south": DemographyRates.zero()},
    )
    trajectory = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 2.0, 0.25),
        EulerSolver(),
    )
    for state in trajectory.states:
        assert region_population(state, "north") == pytest.approx(100.0)


def test_migration_changes_regions_but_conserves_global_population():
    stocks, flows = build_demography_sector(
        REGIONS,
        initial_population=_initial(100.0, 0.0),
        rates_by_region={"north": DemographyRates.zero(), "south": DemographyRates.zero()},
        migration_links=(MigrationLink("north", "south", annual_fraction=0.1),),
    )
    trajectory = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 1.0, 0.25),
        EulerSolver(),
    )
    final = trajectory.states[-1]
    assert region_population(final, "north") < 100.0
    assert region_population(final, "south") > 0.0
    assert global_population(final, REGIONS) == pytest.approx(100.0)


def test_births_and_deaths_are_explicit_external_population_flows():
    rates = DemographyRates.zero(
        birth_rate_per_young_adult=0.02,
        mortality={AgeCohort.YOUNG_ADULT: 0.01},
    )
    initial = {"north": {AgeCohort.YOUNG_ADULT: 100.0}, "south": {}}
    stocks, flows = build_demography_sector(
        REGIONS,
        initial_population=initial,
        rates_by_region={"north": rates, "south": DemographyRates.zero()},
    )
    trajectory = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 1.0, 1.0),
        EulerSolver(),
    )
    assert region_population(trajectory.states[-1], "north") == pytest.approx(101.0)


def test_migration_fraction_cannot_exceed_one_per_year():
    with pytest.raises(ValueError, match="within"):
        MigrationLink("north", "south", annual_fraction=1.01)
