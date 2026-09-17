import pytest

from worldzero.sectors.food_land import (
    FoodProductionParams,
    SoilDynamicsParams,
    allocate_land,
    produce_food,
    update_soil_condition,
)
from worldzero.sectors.water import allocate_water


def _food_params() -> FoodProductionParams:
    return FoodProductionParams(
        base_yield_per_land=2.0,
        managed_input_gain=1.5,
        water_half_saturation=10.0,
        nutrient_half_saturation=5.0,
        energy_half_saturation=5.0,
    )


def test_irrigation_nutrients_and_energy_raise_output_with_diminishing_returns():
    land = allocate_land(total_productive_land=100.0, bioenergy_land=10.0)
    low = produce_food(
        land=land,
        soil_condition=0.8,
        irrigation_water=2.0,
        nutrient_input=1.0,
        energy_input=1.0,
        climate_multiplier=1.0,
        params=_food_params(),
    )
    high = produce_food(
        land=land,
        soil_condition=0.8,
        irrigation_water=20.0,
        nutrient_input=10.0,
        energy_input=10.0,
        climate_multiplier=1.0,
        params=_food_params(),
    )
    assert high.food_output > low.food_output
    assert high.water_consumed == pytest.approx(20.0)
    assert high.nutrient_used == pytest.approx(10.0)
    assert high.energy_used == pytest.approx(10.0)


def test_doubling_already_abundant_water_has_smaller_gain_than_first_increase():
    land = allocate_land(total_productive_land=100.0, bioenergy_land=0.0)

    def output(water: float) -> float:
        return produce_food(
            land=land,
            soil_condition=1.0,
            irrigation_water=water,
            nutrient_input=5.0,
            energy_input=5.0,
            climate_multiplier=1.0,
            params=_food_params(),
        ).food_output

    first_gain = output(10.0) - output(0.0)
    late_gain = output(40.0) - output(20.0)
    assert late_gain < first_gain


def test_bioenergy_land_reduces_food_land_without_hidden_expansion():
    no_bioenergy = allocate_land(total_productive_land=100.0, bioenergy_land=0.0)
    with_bioenergy = allocate_land(total_productive_land=100.0, bioenergy_land=25.0)
    assert no_bioenergy.food_land == pytest.approx(100.0)
    assert with_bioenergy.food_land == pytest.approx(75.0)
    assert with_bioenergy.food_land + with_bioenergy.bioenergy_land == pytest.approx(100.0)


def test_water_shortage_is_rationed_not_created():
    allocation = allocate_water(
        renewable_supply=50.0,
        irrigation_demand=80.0,
        other_demand=20.0,
    )
    assert allocation.total_delivered == pytest.approx(50.0)
    assert allocation.irrigation_delivered == pytest.approx(40.0)
    assert allocation.other_delivered == pytest.approx(10.0)
    assert allocation.unmet_demand == pytest.approx(50.0)
    assert allocation.stress_ratio == pytest.approx(2.0)


def test_soil_recovery_is_gradual_not_instantaneous():
    params = SoilDynamicsParams(degradation_rate=0.2, recovery_rate=0.3)
    degraded = update_soil_condition(
        0.8,
        degradation_pressure=1.0,
        restoration_effort=0.0,
        dt=1.0,
        params=params,
    )
    recovering = update_soil_condition(
        degraded,
        degradation_pressure=0.0,
        restoration_effort=1.0,
        dt=1.0,
        params=params,
    )
    assert degraded < 0.8
    assert degraded < recovering < 1.0
