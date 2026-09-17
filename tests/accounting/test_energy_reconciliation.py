import pytest


def test_energy_sector_own_use_is_counted_once():
    from worldzero.accounting.energy import EnergyAccount

    account = EnergyAccount(
        gross=100.0,
        conversion_loss=10.0,
        sector_own_use=8.0,
        final_energy=82.0,
    )
    result = account.reconcile()
    assert result.difference == pytest.approx(0.0)
    assert result.accounted_total == pytest.approx(100.0)


def test_energy_account_detects_nonconservation():
    from worldzero.accounting.energy import EnergyAccount

    account = EnergyAccount(
        gross=100.0,
        conversion_loss=10.0,
        sector_own_use=8.0,
        final_energy=80.0,
    )
    assert account.reconcile().difference == pytest.approx(2.0)


def test_embodied_transition_energy_cannot_be_subtracted_twice():
    from worldzero.accounting.energy import reconcile_transition_energy

    with pytest.raises(ValueError, match="double-count"):
        reconcile_transition_energy(
            sector_own_use=8.0,
            embodied_energy=5.0,
            industrial_energy_demand_includes_embodied=5.0,
            subtract_embodied_again=True,
        )


def test_transition_energy_reconciliation_records_single_accounting_path():
    from worldzero.accounting.energy import reconcile_transition_energy

    result = reconcile_transition_energy(
        sector_own_use=8.0,
        embodied_energy=5.0,
        industrial_energy_demand_includes_embodied=5.0,
        subtract_embodied_again=False,
    )
    assert result.embodied_energy_counted_once == pytest.approx(5.0)
    assert result.additional_subtraction == pytest.approx(0.0)
