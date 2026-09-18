import csv
import gzip
import io
from pathlib import Path

import pytest
import yaml

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.observations import ObservationClass
from worldzero.data.wpp_age5 import (
    COHORT_POPULATION_FIELDS,
    WPP2024_AGE5_FIELDS,
    extract_macroregion_cohort_population,
    inspect_wpp_age5,
    reconcile_macroregion_cohort_population,
    render_macroregion_cohort_population_csv,
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


def _write_modified_cohort_manifest(path: Path, mutate) -> None:
    payload = yaml.safe_load(COHORTS.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    mutate(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _extract_fixture_cut(path: Path, year: int):
    return extract_macroregion_cohort_population(
        path,
        year=year,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=load_region_mapping_manifest(MAPPING),
        region_set=load_region_set_manifest(REGIONS).region_set,
        cohort_manifest=load_age_cohort_manifest(COHORTS),
    )


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


def test_cohort_manifest_rejects_cross_band_source_group_swap(tmp_path: Path):
    path = tmp_path / "swapped.yaml"

    def mutate(payload: dict) -> None:
        cohorts = payload["cohorts"]
        child_groups = cohorts[0]["source_age_groups"]
        older_groups = cohorts[3]["source_age_groups"]
        child_groups[0], older_groups[0] = older_groups[0], child_groups[0]

    _write_modified_cohort_manifest(path, mutate)
    with pytest.raises(ValueError, match="outside declared cohort bounds"):
        load_age_cohort_manifest(path)


def test_cohort_manifest_requires_exact_frozen_wpp_bin_coverage(tmp_path: Path):
    path = tmp_path / "missing-bin.yaml"

    def mutate(payload: dict) -> None:
        payload["cohorts"][0]["source_age_groups"].remove("0-4")

    _write_modified_cohort_manifest(path, mutate)
    with pytest.raises(ValueError, match="exactly cover the frozen WPP V0 age bins"):
        load_age_cohort_manifest(path)


def test_age5_inspection_and_historical_cut(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    inspection = inspect_wpp_age5(path)
    assert inspection.country_area_locations == 237
    assert inspection.country_rows_2023 == 237 * 21
    assert inspection.country_rows_2026 == 237 * 21
    cut = _extract_fixture_cut(path, 2023)
    assert cut.observation_class is ObservationClass.OFFICIAL_ESTIMATE
    assert cut.validation_eligible
    assert cut.total_population == 237 * 21 * 1000.0
    assert set(cut.values) == set(load_region_set_manifest(REGIONS).region_set.ids)
    assert all(set(region) == set(AgeCohort) for region in cut.values.values())


def test_projection_cut_is_bridge_only(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    cut = _extract_fixture_cut(path, 2026)
    assert cut.observation_class is ObservationClass.PROJECTION
    assert not cut.validation_eligible


def test_cohort_cut_renders_canonical_40_row_csv(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    region_ids = load_region_set_manifest(REGIONS).region_set.ids
    cut = _extract_fixture_cut(path, 2023)
    payload = render_macroregion_cohort_population_csv(cut, region_ids=region_ids)

    assert payload == render_macroregion_cohort_population_csv(cut, region_ids=region_ids)
    assert b"\r\n" not in payload
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    assert tuple(rows[0]) == COHORT_POPULATION_FIELDS
    assert len(rows) == len(region_ids) * len(AgeCohort)
    assert [row["cohort_id"] for row in rows[:4]] == [cohort.value for cohort in AgeCohort]
    assert rows[0]["region_id"] == region_ids[0]
    assert rows[-1]["region_id"] == region_ids[-1]
    assert {row["source_observation_class"] for row in rows} == {"OFFICIAL_ESTIMATE"}
    assert {row["observation_class"] for row in rows} == {"DERIVED"}
    assert {row["validation_eligible"] for row in rows} == {"true"}


def test_cohort_cut_reconciliation_reports_deltas_without_policy(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    region_ids = load_region_set_manifest(REGIONS).region_set.ids
    cut = _extract_fixture_cut(path, 2023)
    expected = {region_id: cut.region_total(region_id) for region_id in region_ids}

    exact = reconcile_macroregion_cohort_population(
        cut,
        region_ids=region_ids,
        expected_region_totals=expected,
    )
    assert exact.global_difference == 0.0
    assert exact.max_abs_region_difference == 0.0

    expected[region_ids[0]] += 5.0
    shifted = reconcile_macroregion_cohort_population(
        cut,
        region_ids=region_ids,
        expected_region_totals=expected,
    )
    assert shifted.region_differences[region_ids[0]] == -5.0
    assert shifted.global_difference == -5.0
    assert shifted.max_abs_region_difference == 5.0
