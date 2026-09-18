import csv
import gzip
from pathlib import Path

import pytest

from worldzero.data.observations import ObservationClass
from worldzero.data.wpp2024 import (
    WPP2024_FIELDS,
    classify_wpp2024_year,
    extract_midyear_population,
    inspect_wpp2024,
)


def _write_fixture(path: Path) -> None:
    rows = []
    for iso3, locid, parent, location, year, value in (
        ("AAA", "1", "10", "Alpha", 2023, "10.5"),
        ("AAA", "1", "10", "Alpha", 2024, "11.0"),
        ("AAA", "1", "10", "Alpha", 2101, ""),
        ("BBB", "2", "20", "Beta", 2023, "20.0"),
        ("BBB", "2", "20", "Beta", 2024, "21.0"),
        ("BBB", "2", "20", "Beta", 2101, ""),
    ):
        row = {field: "" for field in WPP2024_FIELDS}
        row.update(
            {
                "SortOrder": locid,
                "LocID": locid,
                "ISO3_code": iso3,
                "LocTypeID": "4",
                "LocTypeName": "Country/Area",
                "ParentID": parent,
                "Location": location,
                "VarID": "2",
                "Variant": "Medium",
                "Time": str(year),
                "TPopulation1Jan": value or "99.0",
                "TPopulation1July": value,
            }
        )
        rows.append(row)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WPP2024_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_year_classification_preserves_estimate_projection_boundary():
    assert classify_wpp2024_year(2023) is ObservationClass.OFFICIAL_ESTIMATE
    assert classify_wpp2024_year(2024) is ObservationClass.PROJECTION
    with pytest.raises(ValueError, match="1950-2100"):
        classify_wpp2024_year(2101)


def test_historical_population_extract_is_official_estimate_and_validation_eligible(tmp_path: Path):
    path = tmp_path / "wpp.csv.gz"
    _write_fixture(path)
    series = extract_midyear_population(
        path,
        years=(2023,),
        dataset_id="wpp-test",
        content_sha256="a" * 64,
    )
    assert series.observation_class is ObservationClass.OFFICIAL_ESTIMATE
    assert series.validation_eligible
    assert series.geography == ("AAA", "BBB")
    assert series.values == (10_500.0, 20_000.0)


def test_projection_population_extract_is_bridge_only(tmp_path: Path):
    path = tmp_path / "wpp.csv.gz"
    _write_fixture(path)
    series = extract_midyear_population(
        path,
        years=(2024,),
        dataset_id="wpp-test",
        content_sha256="a" * 64,
    )
    assert series.observation_class is ObservationClass.PROJECTION
    assert not series.validation_eligible


def test_estimate_and_projection_years_cannot_share_one_series(tmp_path: Path):
    path = tmp_path / "wpp.csv.gz"
    _write_fixture(path)
    with pytest.raises(ValueError, match="separately"):
        extract_midyear_population(
            path,
            years=(2023, 2024),
            dataset_id="wpp-test",
            content_sha256="a" * 64,
        )


def test_inspection_exposes_2101_as_boundary_rows(tmp_path: Path):
    path = tmp_path / "wpp.csv.gz"
    _write_fixture(path)
    inspection = inspect_wpp2024(path)
    assert inspection.total_rows == 6
    assert inspection.country_area_locations == 2
    assert inspection.country_rows_2101 == 2
    assert "TPopulation1Jan" in inspection.boundary_2101_nonempty_fields
    assert "TPopulation1July" not in inspection.boundary_2101_nonempty_fields
