import pytest

from worldzero.science.lineage import LineageRef, LineageRegistry


def test_derived_sources_can_share_one_upstream_lineage():
    registry = LineageRegistry([
        LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
        LineageRef(source_id="SERIES_B", upstream_lineage_id="ROOT_X"),
    ])
    assert registry.independent_source_count({"SERIES_A", "SERIES_B"}) == 1


def test_distinct_upstream_lineages_count_independently():
    registry = LineageRegistry([
        LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
        LineageRef(source_id="SERIES_B", upstream_lineage_id="ROOT_Y"),
    ])
    assert registry.independent_source_count({"SERIES_A", "SERIES_B"}) == 2


def test_duplicate_source_lineage_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        LineageRegistry([
            LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
            LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_Y"),
        ])


def test_unknown_source_cannot_be_counted():
    registry = LineageRegistry([])
    with pytest.raises(KeyError, match="UNKNOWN"):
        registry.independent_source_count({"UNKNOWN"})
