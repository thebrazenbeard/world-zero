"""Versioned macroregion definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml

from worldzero.core import RegionId


@dataclass(frozen=True, slots=True)
class RegionDefinition:
    region_id: RegionId | str
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "region_id", RegionId(str(self.region_id)))
        if not self.label.strip():
            raise ValueError("region label must be non-empty")


@dataclass(frozen=True, slots=True)
class RegionSet:
    version: str
    regions: tuple[RegionDefinition, ...]

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("region-set version must be non-empty")
        if not self.regions:
            raise ValueError("region set must contain at least one region")
        ids = [str(region.region_id) for region in self.regions]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate region IDs are not allowed")

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(str(region.region_id) for region in self.regions)

    def require(self, region_id: RegionId | str) -> RegionDefinition:
        key = str(RegionId(str(region_id)))
        for region in self.regions:
            if str(region.region_id) == key:
                return region
        raise KeyError(key)


class RegionSetStatus(StrEnum):
    DRAFT = "DRAFT"
    FROZEN = "FROZEN"


@dataclass(frozen=True, slots=True)
class RegionSetManifest:
    schema_version: str
    status: RegionSetStatus
    region_set: RegionSet

    def __post_init__(self) -> None:
        if self.schema_version != "REGION_SET_V1":
            raise ValueError("unsupported region-set schema_version")


def load_region_set_manifest(path: Path) -> RegionSetManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("region-set manifest must be a mapping")
    expected_keys = {"schema_version", "version", "status", "regions"}
    if set(payload) != expected_keys:
        raise ValueError("region-set manifest fields do not match REGION_SET_V1")
    raw_regions = payload["regions"]
    if not isinstance(raw_regions, list):
        raise TypeError("region-set regions must be a list")
    regions: list[RegionDefinition] = []
    for raw in raw_regions:
        if not isinstance(raw, dict) or set(raw) != {"id", "label"}:
            raise ValueError("each region entry requires exactly id and label")
        regions.append(RegionDefinition(str(raw["id"]), str(raw["label"])))
    return RegionSetManifest(
        schema_version=str(payload["schema_version"]),
        status=RegionSetStatus(str(payload["status"])),
        region_set=RegionSet(version=str(payload["version"]), regions=tuple(regions)),
    )
