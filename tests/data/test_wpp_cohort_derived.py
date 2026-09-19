import csv
import hashlib
from pathlib import Path

from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.data.observations import ObservationClass
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort

MANIFEST = Path(
    "data/manifests/WZ_WPP_2024_MACROREGION_COHORT_POPULATION_2026_V1.yaml"
)
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
SOURCE_SHA256 = "a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd"
OUTPUT_SHA256 = "a9ed5b83ca86700f42893e3929929afcded2bf4574b1e9b74807fc736a69a236"


def test_2026_cohort_population_manifest_and_output_are_exact():
    manifest = load_derived_dataset_manifest(MANIFEST)

    assert manifest.dataset_id == "wz-wpp2024-macroregion-cohort-population-2026-v1"
    assert manifest.source_lineage[0].dataset_id == (
        "un-wpp-2024-population-age5-sex-medium-v1"
    )
    assert manifest.source_lineage[0].content_sha256 == SOURCE_SHA256
    assert manifest.transform_code_commit == "6c287ec13e86842d51f91c57e9ee23fb54bea464"
    assert manifest.region_set_version == "WZ_MACROREGION_V0"
    assert manifest.cohort_set_version == "WZ_AGE_COHORT_V0"
    assert manifest.years == (2026,)
    assert manifest.unit == "persons"
    assert manifest.source_observation_class is ObservationClass.PROJECTION
    assert not manifest.validation_eligible

    payload = Path(manifest.output_path).read_bytes()
    assert len(payload) == 2835
    assert manifest.output_length_bytes == len(payload)
    assert hashlib.sha256(payload).hexdigest() == OUTPUT_SHA256
    assert manifest.output_sha256 == OUTPUT_SHA256

    with Path(manifest.output_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    regions = load_region_set_manifest(REGIONS).region_set
    expected_cohorts = {cohort.value for cohort in AgeCohort}
    assert len(rows) == len(regions.ids) * len(AgeCohort)
    assert {row["region_id"] for row in rows} == set(regions.ids)
    for region_id in regions.ids:
        region_rows = [row for row in rows if row["region_id"] == region_id]
        assert {row["cohort_id"] for row in region_rows} == expected_cohorts

    assert all(row["year"] == "2026" for row in rows)
    assert all(row["source_observation_class"] == "PROJECTION" for row in rows)
    assert all(row["observation_class"] == "DERIVED" for row in rows)
    assert all(row["validation_eligible"] == "false" for row in rows)
    assert sum(int(row["population_persons"]) for row in rows) == 8_300_678_587
