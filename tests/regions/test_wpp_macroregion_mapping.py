from dataclasses import replace
from pathlib import Path

import pytest

from worldzero.data.observations import (
    ObservationClass,
    ObservationLineage,
    ObservationSeries,
)
from worldzero.regions.definitions import RegionSetStatus, load_region_set_manifest
from worldzero.regions.mapping import (
    aggregate_grouped_observation,
    load_region_mapping_manifest,
)

REGION_PATH = Path("regions/WZ_MACROREGION_V0.yaml")
MAPPING_PATH = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")


def test_macroregion_manifest_is_frozen_and_label_is_truthful():
    manifest = load_region_set_manifest(REGION_PATH)
    assert manifest.status is RegionSetStatus.FROZEN
    assert len(manifest.region_set.ids) == 10
    europe = manifest.region_set.require("western_northern_europe")
    assert europe.label == "Western, Northern & Southern Europe"


def test_wpp_parent_mapping_covers_exact_source_parent_groups():
    mapping = load_region_mapping_manifest(MAPPING_PATH)
    assert mapping.source_group_count == 22
    assert len(mapping.entries) == 22
    assert len({entry.source_group_id for entry in mapping.entries}) == 22
    assert {entry.target_region_id for entry in mapping.entries} == {
        "north_america",
        "latin_america_caribbean",
        "western_northern_europe",
        "eastern_europe_central_asia",
        "middle_east_north_africa",
        "sub_saharan_africa",
        "south_asia",
        "east_asia",
        "southeast_asia",
        "oceania",
    }


def test_mapping_rejects_nonhex_source_digest():
    mapping = load_region_mapping_manifest(MAPPING_PATH)
    with pytest.raises(ValueError, match="must be hexadecimal"):
        replace(mapping, source_content_sha256="z" * 64)


def test_southern_europe_maps_to_western_northern_europe():
    mapping = load_region_mapping_manifest(MAPPING_PATH)
    entry = mapping.require_source_group("925")
    assert entry.source_group_label == "Southern Europe"
    assert entry.target_region_id == "western_northern_europe"


SOURCE_GROUPS = (
    "918",
    "915",
    "916",
    "931",
    "924",
    "926",
    "925",
    "923",
    "5500",
    "912",
    "922",
    "910",
    "911",
    "913",
    "914",
    "5501",
    "906",
    "920",
    "927",
    "928",
    "954",
    "957",
)


def _source_series() -> ObservationSeries:
    values = {group: 1.0 for group in SOURCE_GROUPS}
    values.update({"924": 5.0, "926": 40.0, "925": 30.0, "923": 20.0, "5500": 10.0})
    return ObservationSeries(
        observable_id="population_midyear",
        observation_class=ObservationClass.OFFICIAL_ESTIMATE,
        unit="persons",
        geography=SOURCE_GROUPS,
        time=tuple(2023 for _ in SOURCE_GROUPS),
        values=tuple(values[group] for group in SOURCE_GROUPS),
        lineage=(ObservationLineage(dataset_id="wpp", content_sha256="a" * 64),),
        validation_eligible=True,
    )


def test_aggregation_conserves_population_and_preserves_validation_status():
    mapping = load_region_mapping_manifest(MAPPING_PATH)
    target = load_region_set_manifest(REGION_PATH).region_set
    result = aggregate_grouped_observation(
        _source_series(),
        mapping=mapping,
        target_region_set=target,
        output_observable_id="population_midyear_macroregion",
        transform_version="1.0.0",
        transform_code_commit="b" * 40,
    )
    assert sum(result.values) == pytest.approx(sum(_source_series().values))
    values = dict(zip(result.geography, result.values, strict=True))
    assert values["western_northern_europe"] == pytest.approx(75.0)
    assert values["eastern_europe_central_asia"] == pytest.approx(30.0)
    assert result.validation_eligible
    assert result.observation_class is ObservationClass.DERIVED


def test_mapping_source_parent_ids_match_admitted_wpp_structure():
    mapping = load_region_mapping_manifest(MAPPING_PATH)
    assert {entry.source_group_id for entry in mapping.entries} == {
        "918", "915", "916", "931", "924", "926", "925", "923", "5500",
        "912", "922", "910", "911", "913", "914", "5501", "906", "920",
        "927", "928", "954", "957",
    }
