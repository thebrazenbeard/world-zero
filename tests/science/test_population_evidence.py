from pathlib import Path

import pytest

from worldzero.science.partitions import (
    assert_no_initialization_holdout_leakage,
    load_partition_set,
)
from worldzero.science.population_evidence import (
    load_population_evidence_catalog,
    verify_population_evidence_catalog,
    verify_population_evidence_partition,
)

CATALOG = Path("science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml")
PARTITIONS = Path("science/partitions/WZ_DEMOGRAPHY_2023_INITIALIZATION_PARTITION_V2.yaml")
LEGACY_HOLDOUT = Path("science/partitions/WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1.yaml")


def test_2023_population_evidence_catalog_is_exact_and_resolvable():
    catalog = load_population_evidence_catalog(CATALOG)
    verified = verify_population_evidence_catalog(root=Path("."), catalog=catalog)

    assert verified.frozen_before_execution is True
    assert len(verified.observations) == 50
    assert {item.evidence_covariance_group_id for item in verified.observations} == {
        "UN_WPP_2024_POPULATION_FAMILY"
    }


def test_2023_demography_partition_types_cohorts_as_initialization_not_holdout():
    catalog = load_population_evidence_catalog(CATALOG)
    partition_set = load_partition_set(PARTITIONS)

    by_id = {item.observation_id: item for item in catalog.observations}
    assert partition_set.frozen_before_execution is True
    assert partition_set.observation_ids == set(by_id)
    assert partition_set.calibration_ids & partition_set.initialization_ids == set()
    assert partition_set.initialization_ids & partition_set.final_holdout_ids == set()
    assert len(partition_set.calibration_ids) == 10
    assert len(partition_set.initialization_ids) == 40
    assert len(partition_set.final_holdout_ids) == 0
    assert {by_id[item].role for item in partition_set.calibration_ids} == {
        "POPULATION_TOTAL"
    }
    assert {by_id[item].role for item in partition_set.initialization_ids} == {
        "POPULATION_COHORT"
    }
    verify_population_evidence_partition(catalog=catalog, partition_set=partition_set)


def test_legacy_2023_cohort_holdout_conflicts_with_current_initialization_use():
    current = load_partition_set(PARTITIONS)
    legacy = load_partition_set(LEGACY_HOLDOUT)

    assert current.initialization_ids == legacy.final_holdout_ids
    with pytest.raises(ValueError, match="initialization/final-holdout overlap"):
        assert_no_initialization_holdout_leakage(
            current.initialization_ids,
            legacy.final_holdout_ids,
        )


def test_population_evidence_rejects_manifest_digest_substitution():
    catalog = load_population_evidence_catalog(CATALOG)
    first = catalog.observations[0]
    tampered = catalog.model_copy(
        update={
            "observations": (
                first.model_copy(update={"manifest_sha256": "0" * 64}),
                *catalog.observations[1:],
            )
        }
    )

    with pytest.raises(ValueError, match="manifest digest mismatch"):
        verify_population_evidence_catalog(root=Path("."), catalog=tampered)



def test_population_partition_rejects_unknown_governed_observation():
    catalog = load_population_evidence_catalog(CATALOG)
    partition_set = load_partition_set(PARTITIONS)
    initialization = partition_set.partitions[1]
    tampered_initialization = initialization.model_copy(
        update={"observation_ids": (*initialization.observation_ids[:-1], "unknown-observation")}
    )
    tampered = partition_set.model_copy(
        update={"partitions": (partition_set.partitions[0], tampered_initialization)}
    )

    with pytest.raises(ValueError, match="unknown observation"):
        verify_population_evidence_partition(catalog=catalog, partition_set=tampered)


def test_population_partition_rejects_unassigned_governed_observation():
    catalog = load_population_evidence_catalog(CATALOG)
    partition_set = load_partition_set(PARTITIONS)
    initialization = partition_set.partitions[1]
    tampered_initialization = initialization.model_copy(
        update={"observation_ids": initialization.observation_ids[:-1]}
    )
    tampered = partition_set.model_copy(
        update={"partitions": (partition_set.partitions[0], tampered_initialization)}
    )

    with pytest.raises(ValueError, match="unassigned observation"):
        verify_population_evidence_partition(catalog=catalog, partition_set=tampered)
