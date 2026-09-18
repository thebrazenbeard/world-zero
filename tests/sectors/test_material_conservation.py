import pytest

from worldzero.sectors.materials import MaterialStepInput, reconcile_material_step


def test_zero_recycling_sends_retired_material_to_documented_loss():
    result = reconcile_material_step(
        MaterialStepInput(
            beginning_in_use=100.0,
            retirement=20.0,
            virgin_extraction=25.0,
            desired_new_in_use=20.0,
            recycling_rate=0.0,
            recycling_yield=0.9,
            processing_loss_fraction=0.2,
        )
    )
    assert result.recovered_secondary == 0.0
    assert result.unrecovered_retirement_loss == pytest.approx(20.0)
    assert result.ending_in_use == pytest.approx(100.0)
    assert result.input_balance_difference == pytest.approx(0.0, abs=1e-12)
    assert result.retirement_balance_difference == pytest.approx(0.0, abs=1e-12)


def test_high_recycling_preserves_mass_with_explicit_losses():
    result = reconcile_material_step(
        MaterialStepInput(
            beginning_in_use=100.0,
            retirement=20.0,
            virgin_extraction=5.0,
            desired_new_in_use=20.0,
            recycling_rate=0.9,
            recycling_yield=0.8,
            processing_loss_fraction=0.1,
        )
    )
    assert result.recovered_secondary == pytest.approx(14.4)
    assert result.recycling_loss == pytest.approx(3.6)
    assert result.unrecovered_retirement_loss == pytest.approx(2.0)
    assert result.input_balance_difference == pytest.approx(0.0, abs=1e-12)
    assert result.retirement_balance_difference == pytest.approx(0.0, abs=1e-12)


def test_material_bottleneck_becomes_unmet_demand_not_negative_inventory():
    result = reconcile_material_step(
        MaterialStepInput(
            beginning_in_use=50.0,
            retirement=0.0,
            virgin_extraction=10.0,
            desired_new_in_use=20.0,
            recycling_rate=0.0,
            recycling_yield=0.0,
            processing_loss_fraction=0.1,
        )
    )
    assert result.actual_new_in_use == pytest.approx(9.0)
    assert result.unmet_new_in_use == pytest.approx(11.0)
    assert result.unused_processed_inventory == pytest.approx(0.0)
    assert result.input_balance_difference == pytest.approx(0.0, abs=1e-12)


def test_retirement_cannot_exceed_material_in_use():
    with pytest.raises(ValueError, match="retirement"):
        reconcile_material_step(
            MaterialStepInput(
                beginning_in_use=10.0,
                retirement=11.0,
                virgin_extraction=0.0,
                desired_new_in_use=0.0,
                recycling_rate=0.0,
                recycling_yield=0.0,
                processing_loss_fraction=0.0,
            )
        )
