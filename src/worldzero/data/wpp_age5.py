"""WPP 2024 five-year age/sex population ingestion for V0 cohorts."""

from __future__ import annotations

import csv
import gzip
import io
from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from worldzero.regions.definitions import RegionSet
from worldzero.sectors.demography import AgeCohort

if TYPE_CHECKING:
    from worldzero.regions.mapping import RegionMappingManifest

from .cohorts import AgeCohortManifest
from .observations import ObservationClass, ObservationLineage
from .wpp2024 import classify_wpp2024_year

WPP2024_AGE5_FIELDS = (
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
    "MidPeriod",
    "AgeGrp",
    "AgeGrpStart",
    "AgeGrpSpan",
    "PopMale",
    "PopFemale",
    "PopTotal",
)

WPP2024_AGE5_VARIANT = "Medium"
COHORT_POPULATION_CSV_FIELDS = (
    "region_id",
    "year",
    "cohort_id",
    "population_persons",
    "source_observation_class",
    "observation_class",
    "validation_eligible",
)


@contextmanager
def _reader(path: Path) -> Iterator[csv.DictReader]:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_AGE5_FIELDS:
            raise ValueError("WPP age5 CSV schema does not match frozen contract")
        yield reader


@contextmanager
def _reader_bytes(payload: bytes) -> Iterator[csv.DictReader]:
    with (
        gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as compressed,
        io.TextIOWrapper(
            compressed,
            encoding="utf-8-sig",
            newline="",
        ) as handle,
    ):
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_AGE5_FIELDS:
            raise ValueError("WPP age5 CSV schema does not match frozen contract")
        yield reader


@dataclass(frozen=True, slots=True)
class WPPAge5Inspection:
    total_rows: int
    country_area_locations: int
    minimum_year: int
    maximum_year: int
    age_groups: tuple[str, ...]
    variants: tuple[str, ...]
    country_rows_2023: int
    country_rows_2026: int


def inspect_wpp_age5(path: Path) -> WPPAge5Inspection:
    total_rows = 0
    countries: set[str] = set()
    years: set[int] = set()
    ages: set[str] = set()
    variants: set[str] = set()
    year_counts = {2023: 0, 2026: 0}
    with _reader(path) as reader:
        for row in reader:
            total_rows += 1
            years.add(int(row["Time"]))
            ages.add(row["AgeGrp"])
            variants.add(row["Variant"])
            if row["ISO3_code"]:
                countries.add(row["ISO3_code"])
                year = int(row["Time"])
                if year in year_counts:
                    year_counts[year] += 1
    return WPPAge5Inspection(
        total_rows=total_rows,
        country_area_locations=len(countries),
        minimum_year=min(years),
        maximum_year=max(years),
        age_groups=tuple(sorted(ages, key=_age_group_sort_key)),
        variants=tuple(sorted(variants)),
        country_rows_2023=year_counts[2023],
        country_rows_2026=year_counts[2026],
    )


def _age_group_sort_key(label: str) -> int:
    if label == "100+":
        return 100
    return int(label.split("-", maxsplit=1)[0])


@dataclass(frozen=True, slots=True)
class CohortPopulationCut:
    year: int
    observation_class: ObservationClass
    validation_eligible: bool
    region_set_version: str
    cohort_set_version: str
    values: Mapping[str, Mapping[AgeCohort, float]]
    lineage: tuple[ObservationLineage, ...]

    @property
    def total_population(self) -> float:
        return sum(
            value for region_values in self.values.values() for value in region_values.values()
        )

    def region_total(self, region_id: str) -> float:
        return sum(self.values[region_id].values())


def _extract_macroregion_cohort_population(
    reader: csv.DictReader,
    *,
    year: int,
    dataset_id: str,
    content_sha256: str,
    region_mapping: RegionMappingManifest,
    region_set: RegionSet,
    cohort_manifest: AgeCohortManifest,
) -> CohortPopulationCut:
    observation_class = classify_wpp2024_year(year)
    source_to_region = region_mapping.source_to_target
    age_to_cohort = cohort_manifest.source_group_to_cohort
    if set(source_to_region.values()) - set(region_set.ids):
        raise ValueError("region mapping references undeclared target region")

    totals: dict[str, dict[AgeCohort, float]] = {
        region_id: {cohort: 0.0 for cohort in AgeCohort} for region_id in region_set.ids
    }
    country_age_counts: defaultdict[str, int] = defaultdict(int)
    seen_parent_groups: set[str] = set()
    seen_age_groups: set[str] = set()
    selected_rows = 0

    for row in reader:
        if row["Time"] != str(year) or not row["ISO3_code"]:
            continue
        if row["Variant"] != WPP2024_AGE5_VARIANT:
            raise ValueError("unexpected WPP age5 variant")
        parent_id = row["ParentID"]
        if parent_id not in source_to_region:
            raise ValueError(f"unmapped WPP parent group: {parent_id}")
        age_group = row["AgeGrp"]
        if age_group not in age_to_cohort:
            raise ValueError(f"unmapped WPP age group: {age_group}")
        raw_value = row["PopTotal"]
        if not raw_value:
            raise ValueError(f"missing PopTotal for {row['ISO3_code']} {year} {age_group}")
        value = float(raw_value) * 1000.0
        if value < 0:
            raise ValueError("WPP age5 population must be nonnegative")
        totals[source_to_region[parent_id]][age_to_cohort[age_group]] += value
        country_age_counts[row["ISO3_code"]] += 1
        seen_parent_groups.add(parent_id)
        seen_age_groups.add(age_group)
        selected_rows += 1

    if len(country_age_counts) != 237:
        raise ValueError("WPP age5 extraction must contain 237 country/area locations")
    expected_age_count = len(age_to_cohort)
    if any(count != expected_age_count for count in country_age_counts.values()):
        raise ValueError("each country/area must contain every frozen age group exactly once")
    if selected_rows != 237 * expected_age_count:
        raise ValueError("unexpected WPP age5 country-row count")
    if seen_parent_groups != set(source_to_region):
        raise ValueError("WPP age5 parent-group coverage is incomplete")
    if seen_age_groups != set(age_to_cohort):
        raise ValueError("WPP age5 age-group coverage is incomplete")

    frozen_values = MappingProxyType(
        {
            region_id: MappingProxyType(dict(region_values))
            for region_id, region_values in totals.items()
        }
    )
    return CohortPopulationCut(
        year=year,
        observation_class=observation_class,
        validation_eligible=(observation_class is ObservationClass.OFFICIAL_ESTIMATE),
        region_set_version=region_set.version,
        cohort_set_version=cohort_manifest.version,
        values=frozen_values,
        lineage=(
            ObservationLineage(
                dataset_id=dataset_id,
                content_sha256=content_sha256,
            ),
        ),
    )


def extract_macroregion_cohort_population(
    path: Path,
    *,
    year: int,
    dataset_id: str,
    content_sha256: str,
    region_mapping: RegionMappingManifest,
    region_set: RegionSet,
    cohort_manifest: AgeCohortManifest,
) -> CohortPopulationCut:
    with _reader(path) as reader:
        return _extract_macroregion_cohort_population(
            reader,
            year=year,
            dataset_id=dataset_id,
            content_sha256=content_sha256,
            region_mapping=region_mapping,
            region_set=region_set,
            cohort_manifest=cohort_manifest,
        )


def extract_macroregion_cohort_population_bytes(
    payload: bytes,
    *,
    year: int,
    dataset_id: str,
    content_sha256: str,
    region_mapping: RegionMappingManifest,
    region_set: RegionSet,
    cohort_manifest: AgeCohortManifest,
) -> CohortPopulationCut:
    """Extract a cohort cut from the exact already-verified gzip payload bytes."""

    with _reader_bytes(payload) as reader:
        return _extract_macroregion_cohort_population(
            reader,
            year=year,
            dataset_id=dataset_id,
            content_sha256=content_sha256,
            region_mapping=region_mapping,
            region_set=region_set,
            cohort_manifest=cohort_manifest,
        )


def render_cohort_population_csv(cut: CohortPopulationCut) -> bytes:
    """Render a cohort cut as deterministic UTF-8 CSV bytes."""

    expected_cohorts = set(AgeCohort)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=COHORT_POPULATION_CSV_FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()

    for region_id, region_values in cut.values.items():
        if set(region_values) != expected_cohorts:
            raise ValueError("cohort population cut must contain every frozen cohort")
        for cohort in AgeCohort:
            value = float(region_values[cohort])
            rounded = round(value)
            if value < 0:
                raise ValueError("cohort population must be nonnegative")
            if abs(value - rounded) > 0.001:
                raise ValueError("cohort population must resolve to whole persons")
            writer.writerow(
                {
                    "region_id": region_id,
                    "year": cut.year,
                    "cohort_id": cohort.value,
                    "population_persons": int(rounded),
                    "source_observation_class": cut.observation_class.value,
                    "observation_class": ObservationClass.DERIVED.value,
                    "validation_eligible": str(cut.validation_eligible).lower(),
                }
            )

    return buffer.getvalue().encode("utf-8")
