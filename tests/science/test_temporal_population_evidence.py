import csv
import json
from pathlib import Path

import pytest

from worldzero.science.partitions import PartitionSet, load_partition_set
from worldzero.science.population_evidence import (
    load_population_evidence_catalog,
    verify_population_evidence_catalog,
    verify_temporal_population_evidence_partition,
)

CATALOG = Path("science/evidence/WZ_DEMOGRAPHY_2022_2023_TEMPORAL_EVIDENCE_V1.yaml")
PARTITIONS = Path("science/partitions/WZ_DEMOGRAPHY_2022_2023_TEMPORAL_HOLDOUT_V1.yaml")


def test_temporal_population_packet_is_exact_resolvable_and_strictly_ordered() -> None:
    catalog = load_population_evidence_catalog(CATALOG)
    verified = verify_population_evidence_catalog(root=Path("."), catalog=catalog)
    partition_set = load_partition_set(PARTITIONS)
    verify_temporal_population_evidence_partition(
        catalog=verified,
        partition_set=partition_set,
    )

    by_id = {item.observation_id: item for item in verified.observations}
    assert len(by_id) == 90
    assert len(partition_set.calibration_ids) == 10
    assert len(partition_set.initialization_ids) == 40
    assert len(partition_set.final_holdout_ids) == 40

    assert {by_id[item].year for item in partition_set.calibration_ids} == {2022}
    assert {by_id[item].role for item in partition_set.calibration_ids} == {
        "POPULATION_TOTAL"
    }
    assert {by_id[item].year for item in partition_set.initialization_ids} == {2022}
    assert {by_id[item].role for item in partition_set.initialization_ids} == {
        "POPULATION_COHORT"
    }
    assert {by_id[item].year for item in partition_set.final_holdout_ids} == {2023}
    assert {by_id[item].role for item in partition_set.final_holdout_ids} == {
        "POPULATION_COHORT"
    }
    assert all(
        not (
            item.year == 2023
            and item.role == "POPULATION_TOTAL"
        )
        for item in verified.observations
    )
    assert {item.evidence_covariance_group_id for item in verified.observations} == {
        "UN_WPP_2024_POPULATION_FAMILY"
    }


def test_temporal_population_packet_rejects_same_year_prefit_evidence() -> None:
    catalog = load_population_evidence_catalog(CATALOG)
    partition_set = load_partition_set(PARTITIONS)
    calibration_id = next(iter(partition_set.calibration_ids))
    observations = tuple(
        item.model_copy(update={"year": 2023})
        if item.observation_id == calibration_id
        else item
        for item in catalog.observations
    )
    tampered = catalog.model_copy(update={"observations": observations})

    with pytest.raises(ValueError, match="strictly after"):
        verify_temporal_population_evidence_partition(
            catalog=tampered,
            partition_set=partition_set,
        )


def test_partition_object_rejects_initialization_holdout_overlap() -> None:
    partition_set = load_partition_set(PARTITIONS)
    initialization = next(
        item for item in partition_set.partitions if item.partition_class == "INITIALIZATION"
    )
    holdout = next(
        item for item in partition_set.partitions if item.partition_class == "TEMPORAL_HOLDOUT"
    )
    duplicated = initialization.observation_ids[0]

    with pytest.raises(ValueError, match="overlap"):
        PartitionSet(
            partition_set_id="tampered",
            partitions=(
                partition_set.partitions[0],
                initialization,
                holdout.model_copy(
                    update={"observation_ids": (duplicated, *holdout.observation_ids)}
                ),
            ),
        )



def test_2022_cohort_total_reconciliation_is_exact_and_descriptive() -> None:
    total_path = Path("data/derived/wpp2024/WZ_MACROREGION_V0_population_2022.csv")
    cohort_path = Path(
        "data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2022.csv"
    )
    report_path = Path(
        "science/reconciliation/WZ_DEMOGRAPHY_2022_COHORT_TOTAL_RECONCILIATION_V1.json"
    )

    with total_path.open(encoding="utf-8", newline="") as handle:
        totals = {
            row["region_id"]: int(row["population_persons"])
            for row in csv.DictReader(handle)
        }
    cohort_totals = {region_id: 0 for region_id in totals}
    with cohort_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cohort_totals[row["region_id"]] += int(row["population_persons"])

    differences = {
        region_id: cohort_totals[region_id] - totals[region_id]
        for region_id in totals
    }
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert differences == report["region_differences_persons"]
    assert sum(differences.values()) == report["global_difference_persons"] == 195
    assert (
        max(abs(value) for value in differences.values())
        == report["max_abs_region_difference_persons"]
        == 50
    )
    assert report["acceptance_policy"] is None
