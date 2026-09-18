"""Strict source-group to World Zero macroregion mappings."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

from worldzero.data.observations import (
    ObservationClass,
    ObservationSeries,
    TransformRecord,
)
from worldzero.regions.definitions import RegionSet


@dataclass(frozen=True, slots=True)
class RegionMappingEntry:
    source_group_id: str
    source_group_label: str
    target_region_id: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.source_group_id.strip():
            raise ValueError("source_group_id must be non-empty")
        if not self.source_group_label.strip():
            raise ValueError("source_group_label must be non-empty")
        if not self.target_region_id.strip():
            raise ValueError("target_region_id must be non-empty")


@dataclass(frozen=True, slots=True)
class RegionMappingManifest:
    schema_version: str
    mapping_id: str
    source_dataset_id: str
    source_content_sha256: str
    source_group_field: str
    source_group_count: int
    target_region_set_version: str
    entries: tuple[RegionMappingEntry, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "REGION_MAPPING_V1":
            raise ValueError("unsupported region-mapping schema_version")
        if self.source_group_count != len(self.entries):
            raise ValueError("source_group_count does not match mapping entries")
        ids = tuple(entry.source_group_id for entry in self.entries)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate source group IDs are not allowed")
        if len(self.source_content_sha256) != 64:
            raise ValueError("source_content_sha256 must be a SHA-256 digest")
        try:
            int(self.source_content_sha256, 16)
        except ValueError as exc:
            raise ValueError("source_content_sha256 must be hexadecimal") from exc

    @property
    def source_to_target(self) -> dict[str, str]:
        return {
            entry.source_group_id: entry.target_region_id
            for entry in self.entries
        }

    def require_source_group(self, source_group_id: str) -> RegionMappingEntry:
        for entry in self.entries:
            if entry.source_group_id == source_group_id:
                return entry
        raise KeyError(source_group_id)


def load_region_mapping_manifest(path: Path) -> RegionMappingManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("region mapping manifest must be a mapping")
    expected = {
        "schema_version",
        "mapping_id",
        "source_dataset_id",
        "source_content_sha256",
        "source_group_field",
        "source_group_count",
        "target_region_set_version",
        "groups",
    }
    if set(payload) != expected:
        raise ValueError("region mapping fields do not match REGION_MAPPING_V1")
    raw_groups = payload["groups"]
    if not isinstance(raw_groups, list):
        raise TypeError("region mapping groups must be a list")
    entries: list[RegionMappingEntry] = []
    for raw in raw_groups:
        if not isinstance(raw, dict):
            raise TypeError("region mapping group must be a mapping")
        allowed = {"source_group_id", "source_group_label", "target_region_id", "notes"}
        if not set(raw) <= allowed:
            raise ValueError("region mapping group contains unknown fields")
        required = {"source_group_id", "source_group_label", "target_region_id"}
        if not required <= set(raw):
            raise ValueError("region mapping group is missing required fields")
        entries.append(
            RegionMappingEntry(
                source_group_id=str(raw["source_group_id"]),
                source_group_label=str(raw["source_group_label"]),
                target_region_id=str(raw["target_region_id"]),
                notes=None if raw.get("notes") is None else str(raw["notes"]),
            )
        )
    return RegionMappingManifest(
        schema_version=str(payload["schema_version"]),
        mapping_id=str(payload["mapping_id"]),
        source_dataset_id=str(payload["source_dataset_id"]),
        source_content_sha256=str(payload["source_content_sha256"]),
        source_group_field=str(payload["source_group_field"]),
        source_group_count=int(payload["source_group_count"]),
        target_region_set_version=str(payload["target_region_set_version"]),
        entries=tuple(entries),
    )


def aggregate_grouped_observation(
    source: ObservationSeries,
    *,
    mapping: RegionMappingManifest,
    target_region_set: RegionSet,
    output_observable_id: str,
    transform_version: str,
    transform_code_commit: str,
) -> ObservationSeries:
    if target_region_set.version != mapping.target_region_set_version:
        raise ValueError("target region-set version does not match mapping")
    target_ids = set(target_region_set.ids)
    unknown_targets = sorted(
        {entry.target_region_id for entry in mapping.entries} - target_ids
    )
    if unknown_targets:
        raise ValueError("mapping references unknown target regions: " + ", ".join(unknown_targets))
    expected_groups = set(mapping.source_to_target)
    by_time: defaultdict[int, dict[str, float]] = defaultdict(dict)
    for source_group, year, value in zip(
        source.geography,
        source.time,
        source.values,
        strict=True,
    ):
        if source_group not in expected_groups:
            raise ValueError(f"unmapped source group: {source_group}")
        if source_group in by_time[year]:
            raise ValueError(f"duplicate source group {source_group} for year {year}")
        by_time[year][source_group] = value

    for year, values in by_time.items():
        missing = sorted(expected_groups - set(values))
        if missing:
            raise ValueError(
                f"missing source groups for year {year}: " + ", ".join(missing)
            )

    output_geography: list[str] = []
    output_time: list[int] = []
    output_values: list[float] = []
    for year in sorted(by_time):
        totals = {region_id: 0.0 for region_id in target_region_set.ids}
        for source_group, value in by_time[year].items():
            totals[mapping.source_to_target[source_group]] += value
        for region_id in target_region_set.ids:
            output_geography.append(region_id)
            output_time.append(year)
            output_values.append(totals[region_id])

    return ObservationSeries(
        observable_id=output_observable_id,
        observation_class=ObservationClass.DERIVED,
        unit=source.unit,
        geography=tuple(output_geography),
        time=tuple(output_time),
        values=tuple(output_values),
        lineage=source.lineage,
        validation_eligible=source.validation_eligible,
        transform=TransformRecord(
            transform_id=mapping.mapping_id,
            version=transform_version,
            code_commit=transform_code_commit,
            source_observable_ids=(source.observable_id,),
        ),
        notes=f"Aggregated from {mapping.source_group_field} using {mapping.mapping_id}",
    )
