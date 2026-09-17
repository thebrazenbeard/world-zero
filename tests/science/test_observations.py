from worldzero.science.types import EvidenceClass


def _mapping(
    observable_id: str,
    *,
    upstream_lineage_id: str = "ROOT_A",
    covariance_group: str | None = None,
):
    from worldzero.science.observations import ObservationMapping

    return ObservationMapping(
        observable_id=observable_id,
        dataset_id=f"DATASET_{observable_id}",
        dataset_digest="a" * 64,
        transform_digest="b" * 64,
        upstream_lineage_id=upstream_lineage_id,
        evidence_class=EvidenceClass.DERIVED,
        unit="index",
        covariance_group=covariance_group,
    )


def test_observation_mapping_preserves_upstream_lineage():
    mapping = _mapping("ENERGY_INTENSITY", upstream_lineage_id="IEA_ROOT_SERIES")
    assert mapping.upstream_lineage_id == "IEA_ROOT_SERIES"


def test_shared_covariance_group_is_not_counted_as_independent_confirmation():
    from worldzero.science.observations import summarize_independence

    summary = summarize_independence(
        [
            _mapping("A", upstream_lineage_id="ROOT_A", covariance_group="ROOT1"),
            _mapping("B", upstream_lineage_id="ROOT_B", covariance_group="ROOT1"),
        ]
    )
    assert summary.observation_count == 2
    assert summary.independent_group_count == 1
    assert summary.shared_group_ids == ("ROOT1",)


def test_shared_upstream_lineage_is_not_independent_without_explicit_covariance_group():
    from worldzero.science.observations import summarize_independence

    summary = summarize_independence(
        [
            _mapping("A", upstream_lineage_id="COMMON_ROOT"),
            _mapping("B", upstream_lineage_id="COMMON_ROOT"),
        ]
    )
    assert summary.independent_group_count == 1
