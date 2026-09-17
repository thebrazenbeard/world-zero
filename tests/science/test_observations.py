import pytest

from worldzero.science.observations import (
    ObservationMapping,
    summarize_independence,
)
from worldzero.science.types import EvidenceClass


def obs(observable_id: str, covariance_group: str | None = None, lineage: str = "ROOT_DEFAULT"):
    return ObservationMapping(
        observable_id=observable_id,
        dataset_id=f"DATASET_{observable_id}",
        dataset_digest="a" * 64,
        transform_digest="b" * 64,
        upstream_lineage_id=lineage,
        evidence_covariance_group_id=covariance_group,
        evidence_class=EvidenceClass.DERIVED,
        unit="1",
    )


def test_observation_mapping_preserves_upstream_lineage():
    mapping = ObservationMapping(
        observable_id="ENERGY_INTENSITY",
        dataset_id="DERIVED_SERIES_A",
        dataset_digest="a" * 64,
        transform_digest="b" * 64,
        upstream_lineage_id="IEA_ROOT_SERIES",
        evidence_class=EvidenceClass.DERIVED,
        unit="MJ/USD",
    )
    assert mapping.upstream_lineage_id == "IEA_ROOT_SERIES"


def test_shared_covariance_group_is_not_counted_as_independent_confirmation():
    summary = summarize_independence(
        [
            obs("a", covariance_group="ROOT1", lineage="LINEAGE_A"),
            obs("b", covariance_group="ROOT1", lineage="LINEAGE_B"),
        ]
    )
    assert summary.observation_count == 2
    assert summary.independent_group_count == 1


def test_upstream_lineage_is_conservative_covariance_fallback():
    summary = summarize_independence([obs("a", lineage="ROOT1"), obs("b", lineage="ROOT1")])
    assert summary.independent_group_count == 1


def test_distinct_lineages_without_covariance_override_count_separately():
    summary = summarize_independence([obs("a", lineage="ROOT1"), obs("b", lineage="ROOT2")])
    assert summary.independent_group_count == 2


def test_duplicate_observable_id_in_one_summary_is_rejected():
    with pytest.raises(ValueError, match="duplicate observable_id"):
        summarize_independence([obs("a"), obs("a")])


def test_non_hex_dataset_digest_is_rejected():
    with pytest.raises(ValueError):
        ObservationMapping(
            observable_id="BAD",
            dataset_id="BAD_DATA",
            dataset_digest="not-a-digest",
            transform_digest="b" * 64,
            upstream_lineage_id="ROOT",
            evidence_class=EvidenceClass.OBSERVED,
            unit="1",
        )
