import pytest

from worldzero.core import ModelState
from worldzero.sectors.distribution import DistributionParams, allocate_income
from worldzero.sectors.production import (
    ProductionParams,
    productive_capital_stock_id,
    region_output,
)


def test_output_is_limited_by_tighter_of_capital_and_labor_capacity():
    params = ProductionParams(
        initial_productive_capital=300.0,
        initial_service_capital=50.0,
        capital_output_ratio=3.0,
        labor_productivity=2.0,
        investment_share=0.2,
        service_investment_fraction=0.25,
        productive_depreciation_rate=0.05,
        service_depreciation_rate=0.04,
    )
    state = ModelState({
        str(productive_capital_stock_id("north")): 300.0,
        "population:north:young_adult": 40.0,
        "population:north:mature_adult": 20.0,
    })
    assert region_output(state, "north", params) == pytest.approx(100.0)


def test_distribution_reallocates_income_without_creating_output():
    low_labor = allocate_income(100.0, DistributionParams(labor_share=0.5))
    high_labor = allocate_income(100.0, DistributionParams(labor_share=0.8))

    assert low_labor.real_output == high_labor.real_output == 100.0
    assert low_labor.labor_income == 50.0
    assert high_labor.labor_income == 80.0
    assert low_labor.owner_income == 50.0
    assert high_labor.owner_income == 20.0
    assert low_labor.labor_income + low_labor.owner_income == pytest.approx(100.0)
    assert high_labor.labor_income + high_labor.owner_income == pytest.approx(100.0)


def test_distribution_rejects_impossible_labor_share():
    with pytest.raises(ValueError, match="labor_share"):
        DistributionParams(labor_share=1.1)
