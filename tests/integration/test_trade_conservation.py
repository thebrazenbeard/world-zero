import pytest

from worldzero.sectors.institutions import InstitutionParams, PolicyIntervention, policy_response
from worldzero.sectors.trade import TradeLink, allocate_physical_trade


def test_policy_intervention_has_no_effect_before_implementation_delay():
    params = InstitutionParams(response_capacity=0.75, implementation_delay=3.0)
    intervention = PolicyIntervention(start_time=10.0, magnitude=0.8)

    assert policy_response(12.99, params, intervention).effective_magnitude == 0.0
    assert policy_response(13.0, params, intervention).effective_magnitude == pytest.approx(0.6)


def test_trade_redistributes_supply_without_creating_matter():
    result = allocate_physical_trade(
        supply_by_region={"a": 100.0, "b": 0.0},
        demand_by_region={"a": 20.0, "b": 70.0},
        links=(TradeLink("a", "b", capacity=80.0, loss_fraction=0.1),),
    )
    assert result.local_consumption["a"] == pytest.approx(20.0)
    assert result.delivered_by_trade["b"] == pytest.approx(70.0)
    assert result.unmet_demand["b"] == pytest.approx(0.0)
    assert result.total_losses > 0.0
    assert result.mass_balance_difference == pytest.approx(0.0, abs=1e-12)


def test_trade_fragmentation_creates_shortage_not_supply():
    open_result = allocate_physical_trade(
        supply_by_region={"a": 100.0, "b": 0.0},
        demand_by_region={"a": 20.0, "b": 50.0},
        links=(TradeLink("a", "b", capacity=60.0, loss_fraction=0.0),),
    )
    fragmented = allocate_physical_trade(
        supply_by_region={"a": 100.0, "b": 0.0},
        demand_by_region={"a": 20.0, "b": 50.0},
        links=(TradeLink("a", "b", capacity=60.0, loss_fraction=0.0, enabled=False),),
    )
    assert open_result.unmet_demand["b"] == 0.0
    assert fragmented.unmet_demand["b"] == pytest.approx(50.0)
    assert fragmented.unused_supply["a"] == pytest.approx(80.0)
    assert fragmented.mass_balance_difference == pytest.approx(0.0, abs=1e-12)
