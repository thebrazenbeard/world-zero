import importlib
import importlib.util

import pytest


def _lineage():
    if importlib.util.find_spec("worldzero.science.lineage") is None:
        pytest.fail("worldzero.science.lineage is not implemented")
    return importlib.import_module("worldzero.science.lineage")


def test_derived_sources_can_share_one_upstream_lineage():
    module = _lineage()
    registry = module.LineageRegistry(
        [
            module.LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
            module.LineageRef(source_id="SERIES_B", upstream_lineage_id="ROOT_X"),
        ]
    )
    assert registry.independent_source_count({"SERIES_A", "SERIES_B"}) == 1


def test_distinct_upstream_lineages_count_independently():
    module = _lineage()
    registry = module.LineageRegistry(
        [
            module.LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
            module.LineageRef(source_id="SERIES_B", upstream_lineage_id="ROOT_Y"),
        ]
    )
    assert registry.independent_source_count({"SERIES_A", "SERIES_B"}) == 2


def test_unknown_source_id_is_rejected():
    module = _lineage()
    registry = module.LineageRegistry(
        [module.LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X")]
    )
    with pytest.raises(KeyError, match="MISSING"):
        registry.independent_source_count({"MISSING"})
