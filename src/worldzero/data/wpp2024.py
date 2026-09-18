"""WPP 2024 bulk-file inspection and population extraction."""

from __future__ import annotations

import csv
import gzip
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .observations import ObservationClass, ObservationLineage, ObservationSeries

WPP2024_ESTIMATE_END_YEAR = 2023
WPP2024_PROJECTION_START_YEAR = 2024
WPP2024_SUBSTANTIVE_END_YEAR = 2100
WPP2024_TECHNICAL_BOUNDARY_YEAR = 2101
WPP2024_VARIANT = "Medium"

WPP2024_FIELDS = (
    "SortOrder",
    "LocID",
    "Notes",
    "ISO3_code",
    "ISO2_code",
    "SDMX_code",
    "LocTypeID",
    "LocTypeName",
    "ParentID",
    "Location",
    "VarID",
    "Variant",
    "Time",
    "TPopulation1Jan",
    "TPopulation1July",
    "TPopulationMale1July",
    "TPopulationFemale1July",
    "PopDensity",
    "PopSexRatio",
    "MedianAgePop",
    "NatChange",
    "NatChangeRT",
    "PopChange",
    "PopGrowthRate",
    "DoublingTime",
    "Births",
    "Births1519",
    "CBR",
    "TFR",
    "NRR",
    "MAC",
    "SRB",
    "Deaths",
    "DeathsMale",
    "DeathsFemale",
    "CDR",
    "LEx",
    "LExMale",
    "LExFemale",
    "LE15",
    "LE15Male",
    "LE15Female",
    "LE65",
    "LE65Male",
    "LE65Female",
    "LE80",
    "LE80Male",
    "LE80Female",
    "InfantDeaths",
    "IMR",
    "LBsurvivingAge1",
    "Under5Deaths",
    "Q5",
    "Q0040",
    "Q0040Male",
    "Q0040Female",
    "Q0060",
    "Q0060Male",
    "Q0060Female",
    "Q1550",
    "Q1550Male",
    "Q1550Female",
    "Q1560",
    "Q1560Male",
    "Q1560Female",
    "NetMigrations",
    "CNMR",
)


@dataclass(frozen=True, slots=True)
class WPP2024Inspection:
    total_rows: int
    unique_locations: int
    country_area_locations: int
    minimum_year: int
    maximum_year: int
    variants: tuple[str, ...]
    country_rows_2023: int
    country_rows_2024: int
    country_rows_2101: int
    boundary_2101_nonempty_fields: tuple[str, ...]


@contextmanager
def _reader(path: Path) -> Iterator[csv.DictReader]:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_FIELDS:
            raise ValueError("WPP2024 CSV schema does not match frozen field contract")
        yield reader


def inspect_wpp2024(path: Path) -> WPP2024Inspection:
    locations: set[str] = set()
    countries: set[str] = set()
    variants: set[str] = set()
    years: list[int] = []
    country_year_counts = {2023: 0, 2024: 0, 2101: 0}
    boundary_fields: set[str] = set()
    total_rows = 0
    with _reader(path) as reader:
        for row in reader:
            total_rows += 1
            locations.add(row["LocID"])
            variants.add(row["Variant"])
            year = int(row["Time"])
            years.append(year)
            if row["ISO3_code"]:
                countries.add(row["ISO3_code"])
                if year in country_year_counts:
                    country_year_counts[year] += 1
                if year == WPP2024_TECHNICAL_BOUNDARY_YEAR:
                    boundary_fields.update(key for key, value in row.items() if value != "")

    return WPP2024Inspection(
        total_rows=total_rows,
        unique_locations=len(locations),
        country_area_locations=len(countries),
        minimum_year=min(years),
        maximum_year=max(years),
        variants=tuple(sorted(variants)),
        country_rows_2023=country_year_counts[2023],
        country_rows_2024=country_year_counts[2024],
        country_rows_2101=country_year_counts[2101],
        boundary_2101_nonempty_fields=tuple(sorted(boundary_fields)),
    )


def classify_wpp2024_year(year: int) -> ObservationClass:
    if year < 1950 or year > WPP2024_SUBSTANTIVE_END_YEAR:
        raise ValueError("WPP2024 substantive year must be within 1950-2100")
    if year <= WPP2024_ESTIMATE_END_YEAR:
        return ObservationClass.OFFICIAL_ESTIMATE
    return ObservationClass.PROJECTION


def extract_midyear_population(
    path: Path,
    *,
    years: tuple[int, ...],
    dataset_id: str,
    content_sha256: str,
    iso3_codes: tuple[str, ...] | None = None,
) -> ObservationSeries:
    if not years:
        raise ValueError("population extraction requires at least one year")
    if len(years) != len(set(years)):
        raise ValueError("population extraction years must be unique")
    classes = {classify_wpp2024_year(year) for year in years}
    if len(classes) != 1:
        raise ValueError("WPP estimate and projection years must be extracted separately")
    observation_class = classes.pop()
    requested_iso3 = None if iso3_codes is None else set(iso3_codes)
    if requested_iso3 is not None and len(requested_iso3) != len(iso3_codes or ()):
        raise ValueError("ISO3 filters must be unique")
    selected: list[tuple[str, int, float]] = []
    requested_years = set(years)
    with _reader(path) as reader:
        for row in reader:
            iso3 = row["ISO3_code"]
            if not iso3:
                continue
            if requested_iso3 is not None and iso3 not in requested_iso3:
                continue
            year = int(row["Time"])
            if year not in requested_years:
                continue
            if row["Variant"] != WPP2024_VARIANT:
                raise ValueError("unexpected WPP variant in medium bulk file")
            raw_value = row["TPopulation1July"]
            if not raw_value:
                raise ValueError(f"missing mid-year population for {iso3} {year}")
            selected.append((iso3, year, float(raw_value) * 1000.0))

    if not selected:
        raise ValueError("population extraction matched no country/area rows")
    selected.sort(key=lambda item: (item[0], item[1]))
    if requested_iso3 is not None:
        present = {item[0] for item in selected}
        missing = sorted(requested_iso3 - present)
        if missing:
            raise ValueError("missing requested ISO3 locations: " + ", ".join(missing))
    return ObservationSeries(
        observable_id="population_midyear",
        observation_class=observation_class,
        unit="persons",
        geography=tuple(item[0] for item in selected),
        time=tuple(item[1] for item in selected),
        values=tuple(item[2] for item in selected),
        lineage=(
            ObservationLineage(
                dataset_id=dataset_id,
                content_sha256=content_sha256,
            ),
        ),
        validation_eligible=(observation_class is ObservationClass.OFFICIAL_ESTIMATE),
        notes=(
            "UN WPP 2024 official estimate period"
            if observation_class is ObservationClass.OFFICIAL_ESTIMATE
            else "UN WPP 2024 projection bridge; not validation evidence"
        ),
    )
