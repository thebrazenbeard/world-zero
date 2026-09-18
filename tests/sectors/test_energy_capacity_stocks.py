import pytest

from worldzero.core import RK4Solver, SimulationClock, StockFlowModel, solve
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.energy import (
    EnergyBuildParams,
    build_energy_sector,
    cumulative_low_carbon_stock_id,
    energy_capacity_from_state,
    low_carbon_capacity_stock_id,
)

REGIONS = RegionSet(version="energy-test", regions=(RegionDefinition("r1", "R1"),))


def _params() -> EnergyBuildParams:
    return EnergyBuildParams(
        initial_fossil_capacity=100.0,
        initial_low_carbon_capacity=10.0,
        initial_grid_capacity=20.0,
        initial_storage_capacity=2.0,
        initial_cumulative_low_carbon=10.0,
        annual_low_carbon_build=4.0,
        annual_grid_build=2.0,
        annual_storage_build=1.0,
        fossil_retirement_rate=0.1,
        low_carbon_retirement_rate=0.0,
        low_carbon_capacity_factor=0.5,
    )


def test_low_carbon_build_updates_installed_and_cumulative_capacity():
    stocks, flows = build_energy_sector(REGIONS, {"r1": _params()})
    result = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 1.0, 0.25),
        RK4Solver(),
    )
    final = result.states[-1]
    assert final.value(low_carbon_capacity_stock_id("r1")) == pytest.approx(14.0)
    assert final.value(cumulative_low_carbon_stock_id("r1")) == pytest.approx(14.0)


def test_fossil_capacity_retires_without_reducing_cumulative_clean_deployment():
    stocks, flows = build_energy_sector(REGIONS, {"r1": _params()})
    result = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 2.0, 0.25),
        RK4Solver(),
    )
    first = energy_capacity_from_state(result.states[0], "r1", _params())
    final = energy_capacity_from_state(result.states[-1], "r1", _params())
    assert final.fossil_useful_capacity < first.fossil_useful_capacity
    assert final.low_carbon_generation_capacity > first.low_carbon_generation_capacity
    assert result.states[-1].value(cumulative_low_carbon_stock_id("r1")) == pytest.approx(18.0)
