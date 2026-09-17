import math

import pytest

from worldzero.core.interfaces import FlowId, Quantity, RegionId, SectorId, StockId


@pytest.mark.parametrize("id_type", [StockId, FlowId, SectorId, RegionId])
def test_ids_are_nonempty_strings(id_type):
    value = id_type("alpha")
    assert str(value) == "alpha"


@pytest.mark.parametrize("id_type", [StockId, FlowId, SectorId, RegionId])
def test_ids_reject_empty_or_whitespace(id_type):
    with pytest.raises(ValueError):
        id_type("   ")


def test_quantity_requires_finite_value_and_unit():
    assert Quantity(3.5, "people").value == 3.5
    with pytest.raises(ValueError):
        Quantity(math.nan, "people")
    with pytest.raises(ValueError):
        Quantity(1.0, "")
