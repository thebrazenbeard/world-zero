import pytest

from worldzero.sectors.energy import EnergyCapacity, dispatch_useful_energy
from worldzero.sectors.technology import LearningCurve


def test_learning_curve_reduces_cost_by_declared_rate_each_doubling():
    curve = LearningCurve(
        reference_cost=100.0,
        reference_cumulative_capacity=10.0,
        learning_rate=0.2,
        floor_fraction=0.4,
    )
    assert curve.unit_cost(10.0) == pytest.approx(100.0)
    assert curve.unit_cost(20.0) == pytest.approx(80.0)
    assert curve.unit_cost(40.0) == pytest.approx(64.0)


def test_learning_curve_respects_floor_and_zero_learning():
    saturated = LearningCurve(100.0, 1.0, learning_rate=0.5, floor_fraction=0.3)
    assert saturated.unit_cost(1e9) == pytest.approx(30.0)

    flat = LearningCurve(100.0, 1.0, learning_rate=0.0, floor_fraction=0.1)
    assert flat.unit_cost(1024.0) == pytest.approx(100.0)


def test_grid_bottleneck_caps_deliverable_low_carbon_energy():
    result = dispatch_useful_energy(
        demand=120.0,
        capacity=EnergyCapacity(
            fossil_useful_capacity=100.0,
            low_carbon_generation_capacity=100.0,
            low_carbon_capacity_factor=0.8,
            grid_delivery_capacity=30.0,
            storage_power_capacity=10.0,
        ),
    )
    assert result.low_carbon_available == pytest.approx(30.0)
    assert result.fossil_dispatched == pytest.approx(90.0)
    assert result.unserved_demand == pytest.approx(0.0)


def test_energy_dispatch_exposes_shortage_instead_of_creating_supply():
    result = dispatch_useful_energy(
        demand=100.0,
        capacity=EnergyCapacity(
            fossil_useful_capacity=20.0,
            low_carbon_generation_capacity=30.0,
            low_carbon_capacity_factor=1.0,
            grid_delivery_capacity=30.0,
            storage_power_capacity=0.0,
        ),
    )
    assert result.total_delivered == pytest.approx(50.0)
    assert result.unserved_demand == pytest.approx(50.0)
