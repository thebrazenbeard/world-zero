import pytest

from worldzero.core import RK4Solver, SimulationClock, StockFlowModel, solve
from worldzero.regions.definitions import RegionDefinition, RegionSet
from worldzero.sectors.materials import (
    MaterialStockParams,
    build_material_sector,
    material_in_use_stock_id,
    material_waste_stock_id,
    total_material_stock,
)

REGIONS = RegionSet(version="material-test", regions=(RegionDefinition("r1", "R1"),))


def _params(recycling_rate: float = 0.3) -> MaterialStockParams:
    return MaterialStockParams(
        initial_virgin_resource=1000.0,
        initial_in_use=100.0,
        initial_waste=20.0,
        initial_lost=0.0,
        extraction_fraction=0.02,
        processing_yield=0.9,
        retirement_rate=0.05,
        recycling_rate=recycling_rate,
        recycling_yield=0.8,
    )


def test_material_stock_loop_conserves_total_material():
    stocks, flows = build_material_sector(REGIONS, {"r1": _params()})
    result = solve(
        StockFlowModel(stocks=stocks, flows=flows),
        SimulationClock(0.0, 5.0, 0.25),
        RK4Solver(),
    )
    totals = [total_material_stock(state, "r1") for state in result.states]
    assert all(value == pytest.approx(totals[0], abs=1e-9) for value in totals)


def test_recycling_moves_material_from_waste_back_to_use():
    with_recycling = _params(recycling_rate=0.5)
    without_recycling = _params(recycling_rate=0.0)

    def run(params: MaterialStockParams):
        stocks, flows = build_material_sector(REGIONS, {"r1": params})
        return solve(
            StockFlowModel(stocks=stocks, flows=flows),
            SimulationClock(0.0, 2.0, 0.25),
            RK4Solver(),
        ).states[-1]

    recycled = run(with_recycling)
    unrecycled = run(without_recycling)
    assert recycled.value(material_in_use_stock_id("r1")) > unrecycled.value(
        material_in_use_stock_id("r1")
    )
    assert recycled.value(material_waste_stock_id("r1")) < unrecycled.value(
        material_waste_stock_id("r1")
    )
