import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.data.manifests import DatasetAdmissionStatus
from worldzero.data.observations import ObservationClass
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort

MANIFEST = Path(
    "data/manifests/WZ_WPP_2024_MACROREGION_COHORT_POPULATION_2023_V1.yaml"
)
TOTAL_POPULATION = Path("data/derived/wpp2024/WZ_MACROREGION_V0_population_2023.csv")
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
SOURCE_SHA256 = "a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd"
OUTPUT_SHA256 = "e42aee90f156e51471c2c1704492b412626dc647fb5e6b4bde6b8b43d9a486d4"


def test_2023_cohort_population_is_exact_validation_eligible_history():
    manifest = load_derived_dataset_manifest(MANIFEST)

    assert manifest.dataset_id == "wz-wpp2024-macroregion-cohort-population-2023-v1"
    assert manifest.source_lineage[0].dataset_id == (
        "un-wpp-2024-population-age5-sex-medium-v1"
    )
    assert manifest.source_lineage[0].content_sha256 == SOURCE_SHA256
    assert manifest.transform_code_commit == "6c287ec13e86842d51f91c57e9ee23fb54bea464"
    assert manifest.region_set_version == "WZ_MACROREGION_V0"
    assert manifest.cohort_set_version == "WZ_AGE_COHORT_V0"
    assert manifest.years == (2023,)
    assert manifest.unit == "persons"
    assert manifest.source_observation_class is ObservationClass.OFFICIAL_ESTIMATE
    assert manifest.validation_eligible
    assert manifest.admission_status is DatasetAdmissionStatus.ADMITTED

    payload = Path(manifest.output_path).read_bytes()
    assert len(payload) == 3074
    assert manifest.output_length_bytes == len(payload)
    assert hashlib.sha256(payload).hexdigest() == OUTPUT_SHA256
    assert manifest.output_sha256 == OUTPUT_SHA256


def test_2023_cohort_population_covers_frozen_subject_and_reconciles():
    manifest = load_derived_dataset_manifest(MANIFEST)

    with Path(manifest.output_path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with TOTAL_POPULATION.open("r", encoding="utf-8", newline="") as handle:
        total_rows = list(csv.DictReader(handle))

    regions = load_region_set_manifest(REGIONS).region_set
    expected_cohorts = {cohort.value for cohort in AgeCohort}
    assert len(rows) == len(regions.ids) * len(AgeCohort)
    assert {row["region_id"] for row in rows} == set(regions.ids)

    cohort_totals: dict[str, int] = defaultdict(int)
    for region_id in regions.ids:
        region_rows = [row for row in rows if row["region_id"] == region_id]
        assert {row["cohort_id"] for row in region_rows} == expected_cohorts
        assert all(row["year"] == "2023" for row in region_rows)
        assert all(
            row["source_observation_class"] == "OFFICIAL_ESTIMATE"
            for row in region_rows
        )
        assert all(row["observation_class"] == "DERIVED" for row in region_rows)
        assert all(row["validation_eligible"] == "true" for row in region_rows)
        cohort_totals[region_id] = sum(
            int(row["population_persons"]) for row in region_rows
        )

    admitted_totals = {
        row["region_id"]: int(row["population_persons"]) for row in total_rows
    }
    assert set(admitted_totals) == set(regions.ids)
    differences = {
        region_id: cohort_totals[region_id] - admitted_totals[region_id]
        for region_id in regions.ids
    }
    assert sum(cohort_totals.values()) == 8_091_735_125
    assert sum(differences.values()) == 194
    assert max(abs(value) for value in differences.values()) == 61
    assert all(abs(value) <= 100 for value in differences.values())
