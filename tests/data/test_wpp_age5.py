import csv
import gzip
from pathlib import Path

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.observations import ObservationClass
from worldzero.data.wpp_age5 import (
    WPP2024_AGE5_FIELDS,
    extract_macroregion_cohort_population,
    inspect_wpp_age5,
)
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import load_region_mapping_manifest
from worldzero.sectors.demography import AgeCohort

COHORTS = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
MAPPING = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")


def _write_fixture(path: Path) -> None:
    mapping = load_region_mapping_manifest(MAPPING)
    parent_ids = tuple(entry.source_group_id for entry in mapping.entries)
    ages = load_age_cohort_manifest(COHORTS).source_group_to_cohort
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WPP2024_AGE5_FIELDS, lineterminator="\n")
        writer.writeheader()
        for index in range(237):
            iso3 = f"X{index:02d}" if index < 100 else f"Y{index:03d}"
            parent_id = parent_ids[index % len(parent_ids)]
            for year in (2023, 2026):
                for age_group in ages:
                    row = {field: "" for field in WPP2024_AGE5_FIELDS}
                    row.update(
                        {
                            "ISO3_code": iso3,
                            "ParentID": parent_id,
                            "Location": iso3,
                            "VarID": "2",
                            "Variant": "Medium",
                            "Time": str(year),
                            "AgeGrp": age_group,
                            "AgeGrpStart": "0",
                            "AgeGrpSpan": "5",
                            "PopMale": "0.4",
                            "PopFemale": "0.6",
                            "PopTotal": "1.0",
                        }
                    )
                    writer.writerow(row)


def test_cohort_manifest_freezes_four_contiguous_v0_bands():
    manifest = load_age_cohort_manifest(COHORTS)
    assert tuple(item.cohort for item in manifest.cohorts) == tuple(AgeCohort)
    assert manifest.cohorts[0].age_min == 0
    assert manifest.cohorts[0].age_max == 14
    assert manifest.cohorts[1].age_min == 15
    assert manifest.cohorts[1].age_max == 39
    assert manifest.cohorts[2].age_min == 40
    assert manifest.cohorts[2].age_max == 64
    assert manifest.cohorts[3].age_min == 65
    assert manifest.cohorts[3].age_max is None
    assert len(manifest.source_group_to_cohort) == 21


def test_age5_inspection_and_historical_cut(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    inspection = inspect_wpp_age5(path)
    assert inspection.country_area_locations == 237
    assert inspection.country_rows_2023 == 237 * 21
    assert inspection.country_rows_2026 == 237 * 21
    cut = extract_macroregion_cohort_population(
        path,
        year=2023,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=load_region_mapping_manifest(MAPPING),
        region_set=load_region_set_manifest(REGIONS).region_set,
        cohort_manifest=load_age_cohort_manifest(COHORTS),
    )
    assert cut.observation_class is ObservationClass.OFFICIAL_ESTIMATE
    assert cut.validation_eligible
    assert cut.total_population == 237 * 21 * 1000.0
    assert set(cut.values) == set(load_region_set_manifest(REGIONS).region_set.ids)
    assert all(set(region) == set(AgeCohort) for region in cut.values.values())


def test_projection_cut_is_bridge_only(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    cut = extract_macroregion_cohort_population(
        path,
        year=2026,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=load_region_mapping_manifest(MAPPING),
        region_set=load_region_set_manifest(REGIONS).region_set,
        cohort_manifest=load_age_cohort_manifest(COHORTS),
    )
    assert cut.observation_class is ObservationClass.PROJECTION
    assert not cut.validation_eligible
