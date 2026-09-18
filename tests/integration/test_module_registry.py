import pytest

from worldzero.models.registry import ModelContribution, ModuleRegistry


def test_module_registry_preserves_declared_module_order():
    registry = ModuleRegistry()
    registry.add(ModelContribution("demography", stocks=(), flows=()))
    registry.add(ModelContribution("energy", stocks=(), flows=()))
    assert registry.module_ids == ("demography", "energy")
    stocks, flows = registry.compose()
    assert stocks == ()
    assert flows == ()


def test_module_registry_rejects_duplicate_module_ownership():
    registry = ModuleRegistry()
    registry.add(ModelContribution("energy", stocks=(), flows=()))
    with pytest.raises(ValueError, match="duplicate module"):
        registry.add(ModelContribution("energy", stocks=(), flows=()))
