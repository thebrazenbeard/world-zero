import csv
import gzip
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.manifests import load_dataset_manifest
from worldzero.data.observations import ObservationClass
from worldzero.data.wpp_age5 import (
    COHORT_POPULATION_CSV_FIELDS,
    WPP2024_AGE5_FIELDS,
    extract_macroregion_cohort_population,
    extract_macroregion_cohort_population_bytes,
    inspect_wpp_age5,
    reconcile_macroregion_cohort_population,
    render_cohort_population_csv,
    validate_wpp_age5_mapping_compatibility,
)
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import load_region_mapping_manifest
from worldzero.sectors.demography import AgeCohort

COHORTS = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
MAPPING = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")
RAW_MANIFEST = Path("data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml")
MAPPING_SOURCE_MANIFEST = Path(
    "data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml"
)


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


def _write_duplicate_missing_age_fixture(path: Path) -> None:
    _write_fixture(path)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = tuple(reader.fieldnames or ())

    ages = tuple(load_age_cohort_manifest(COHORTS).source_group_to_cohort)
    assert len(ages) >= 2
    changed = False
    for row in rows:
        if (
            row["ISO3_code"] == "X00"
            and row["Time"] == "2026"
            and row["AgeGrp"] == ages[1]
        ):
            row["AgeGrp"] = ages[0]
            changed = True
            break
    assert changed

    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_inconsistent_parent_fixture(path: Path) -> None:
    _write_fixture(path)
    mapping = load_region_mapping_manifest(MAPPING)
    parent_ids = tuple(entry.source_group_id for entry in mapping.entries)
    assert len(parent_ids) >= 2

    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = tuple(reader.fieldnames or ())

    changed = False
    original_parent: str | None = None
    for row in rows:
        if row["ISO3_code"] == "X00" and row["Time"] == "2026":
            if original_parent is None:
                original_parent = row["ParentID"]
                continue
            row["ParentID"] = next(parent for parent in parent_ids if parent != original_parent)
            changed = True
            break
    assert changed

    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_modified_cohort_manifest(path: Path, mutate) -> None:
    payload = yaml.safe_load(COHORTS.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    mutate(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_age5_mapping_reuse_is_bound_to_admitted_sibling_source():
    mapping = load_region_mapping_manifest(MAPPING)
    mapping_source = load_dataset_manifest(MAPPING_SOURCE_MANIFEST)
    age5_source = load_dataset_manifest(RAW_MANIFEST)

    validate_wpp_age5_mapping_compatibility(
        mapping_source_manifest=mapping_source,
        age5_manifest=age5_source,
        region_mapping=mapping,
    )

    with pytest.raises(ValueError, match="source digest"):
        validate_wpp_age5_mapping_compatibility(
            mapping_source_manifest=mapping_source,
            age5_manifest=age5_source,
            region_mapping=replace(mapping, source_content_sha256="0" * 64),
        )
    with pytest.raises(ValueError, match="must use ParentID"):
        validate_wpp_age5_mapping_compatibility(
            mapping_source_manifest=mapping_source,
            age5_manifest=age5_source,
            region_mapping=replace(mapping, source_group_field="LocID"),
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


def test_extraction_rejects_duplicate_and_missing_country_age_groups(tmp_path: Path):
    path = tmp_path / "age5-duplicate.csv.gz"
    _write_duplicate_missing_age_fixture(path)

    with pytest.raises(ValueError, match="duplicate WPP age group"):
        extract_macroregion_cohort_population(
            path,
            year=2026,
            dataset_id="age5-test",
            content_sha256="a" * 64,
            region_mapping=load_region_mapping_manifest(MAPPING),
            region_set=load_region_set_manifest(REGIONS).region_set,
            cohort_manifest=load_age_cohort_manifest(COHORTS),
        )


def test_extraction_rejects_country_split_across_parent_groups(tmp_path: Path):
    path = tmp_path / "age5-parent-split.csv.gz"
    _write_inconsistent_parent_fixture(path)

    with pytest.raises(ValueError, match="inconsistent WPP parent group"):
        extract_macroregion_cohort_population(
            path,
            year=2026,
            dataset_id="age5-test",
            content_sha256="a" * 64,
            region_mapping=load_region_mapping_manifest(MAPPING),
            region_set=load_region_set_manifest(REGIONS).region_set,
            cohort_manifest=load_age_cohort_manifest(COHORTS),
        )


def test_cohort_cut_csv_is_deterministic_and_semantically_labeled(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    cut = extract_macroregion_cohort_population(
        path,
        year=2023,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=load_region_mapping_manifest(MAPPING),
        region_set=load_region_set_manifest(REGIONS).region_set,
        cohort_manifest=load_age_cohort_manifest(COHORTS),
    )
    first = render_cohort_population_csv(cut)
    second = render_cohort_population_csv(cut)
    assert first == second
    lines = first.decode("utf-8").splitlines()
    assert lines[0] == ",".join(COHORT_POPULATION_CSV_FIELDS)
    assert len(lines) == 1 + 10 * 4
    assert lines[1].startswith("north_america,2023,child,")
    assert lines[1].endswith(",OFFICIAL_ESTIMATE,DERIVED,true")


def test_verified_payload_bytes_match_path_extraction(tmp_path: Path):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    payload = path.read_bytes()
    mapping = load_region_mapping_manifest(MAPPING)
    regions = load_region_set_manifest(REGIONS).region_set
    cohorts = load_age_cohort_manifest(COHORTS)

    from_path = extract_macroregion_cohort_population(
        path,
        year=2026,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=mapping,
        region_set=regions,
        cohort_manifest=cohorts,
    )
    from_bytes = extract_macroregion_cohort_population_bytes(
        payload,
        year=2026,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=mapping,
        region_set=regions,
        cohort_manifest=cohorts,
    )

    assert render_cohort_population_csv(from_bytes) == render_cohort_population_csv(from_path)


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
    rendered = render_cohort_population_csv(cut).decode("utf-8")
    assert ",PROJECTION,DERIVED,false" in rendered


def test_cohort_reconciliation_reports_deltas_without_setting_acceptance_policy(
    tmp_path: Path,
):
    path = tmp_path / "age5.csv.gz"
    _write_fixture(path)
    regions = load_region_set_manifest(REGIONS).region_set
    cut = extract_macroregion_cohort_population(
        path,
        year=2023,
        dataset_id="age5-test",
        content_sha256="a" * 64,
        region_mapping=load_region_mapping_manifest(MAPPING),
        region_set=regions,
        cohort_manifest=load_age_cohort_manifest(COHORTS),
    )
    expected = {region_id: cut.region_total(region_id) for region_id in regions.ids}

    exact = reconcile_macroregion_cohort_population(
        cut,
        region_ids=regions.ids,
        expected_region_totals=expected,
    )
    assert exact.global_difference == 0.0
    assert exact.max_abs_region_difference == 0.0

    expected[regions.ids[0]] += 5.0
    shifted = reconcile_macroregion_cohort_population(
        cut,
        region_ids=regions.ids,
        expected_region_totals=expected,
    )
    assert shifted.region_differences[regions.ids[0]] == -5.0
    assert shifted.global_difference == -5.0
    assert shifted.max_abs_region_difference == 5.0

    bad = dict(expected)
    bad[regions.ids[0]] = float("nan")
    with pytest.raises(ValueError, match="finite and nonnegative"):
        reconcile_macroregion_cohort_population(
            cut,
            region_ids=regions.ids,
            expected_region_totals=bad,
        )
