from pathlib import Path

import pytest

from worldzero.science.partitions import load_partition_set
from worldzero.science.population_evidence import (
    load_population_evidence_catalog,
    verify_population_evidence_catalog,
)

CATALOG = Path("science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml")
PARTITIONS = Path("science/partitions/WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1.yaml")


def test_2023_population_evidence_catalog_is_exact_and_resolvable():
    catalog = load_population_evidence_catalog(CATALOG)
    verified = verify_population_evidence_catalog(root=Path("."), catalog=catalog)

    assert verified.frozen_before_execution is True
    assert len(verified.observations) == 50
    assert {item.evidence_covariance_group_id for item in verified.observations} == {
        "UN_WPP_2024_POPULATION_FAMILY"
    }


def test_2023_demography_partition_freezes_total_calibration_and_cohort_holdout():
    catalog = load_population_evidence_catalog(CATALOG)
    partition_set = load_partition_set(PARTITIONS)

    by_id = {item.observation_id: item for item in catalog.observations}
    assert partition_set.frozen_before_execution is True
    assert partition_set.calibration_ids | partition_set.final_holdout_ids == set(by_id)
    assert partition_set.calibration_ids & partition_set.final_holdout_ids == set()
    assert len(partition_set.calibration_ids) == 10
    assert len(partition_set.final_holdout_ids) == 40
    assert {by_id[item].role for item in partition_set.calibration_ids} == {
        "POPULATION_TOTAL"
    }
    assert {by_id[item].role for item in partition_set.final_holdout_ids} == {
        "POPULATION_COHORT"
    }


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
