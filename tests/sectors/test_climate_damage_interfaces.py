import pytest

from worldzero.sectors.climate import (
    ClimateParams,
    ClimateState,
    LinearDamage,
    QuadraticDamage,
    step_climate,
)


def test_zero_emissions_relaxes_climate_state_toward_zero():
    params = ClimateParams(
        airborne_fraction=0.5,
        carbon_decay_rate=0.02,
        carbon_doubling_burden=100.0,
        climate_sensitivity=3.0,
        thermal_response_time=20.0,
    )
    initial = ClimateState(carbon_burden=100.0, temperature_anomaly=2.0)
    state = initial
    for _ in range(200):
        state = step_climate(state, emissions=0.0, dt=1.0, params=params)
    assert state.carbon_burden < initial.carbon_burden
    assert state.temperature_anomaly < initial.temperature_anomaly


def test_emissions_raise_carbon_and_temperature_over_time():
    params = ClimateParams(0.5, 0.01, 100.0, 3.0, 10.0)
    state = ClimateState(carbon_burden=0.0, temperature_anomaly=0.0)
    for _ in range(20):
        state = step_climate(state, emissions=10.0, dt=1.0, params=params)
    assert state.carbon_burden > 0.0
    assert state.temperature_anomaly > 0.0


def test_damage_functions_are_pluggable_and_bounded():
    linear = LinearDamage(slope=0.05, floor=0.4)
    quadratic = QuadraticDamage(linear=0.01, quadratic=0.03, floor=0.4)

    assert linear.multiplier(0.0) == pytest.approx(1.0)
    assert quadratic.multiplier(0.0) == pytest.approx(1.0)
    assert linear.multiplier(3.0) != pytest.approx(quadratic.multiplier(3.0))
    assert 0.4 <= linear.multiplier(100.0) <= 1.0
    assert 0.4 <= quadratic.multiplier(100.0) <= 1.0


def test_climate_module_returns_state_not_embedded_food_damage():
    params = ClimateParams(0.5, 0.01, 100.0, 3.0, 10.0)
    state = step_climate(
        ClimateState(carbon_burden=50.0, temperature_anomaly=1.0),
        emissions=5.0,
        dt=1.0,
        params=params,
    )
    assert isinstance(state, ClimateState)
    assert not hasattr(state, "food_damage")
