"""Observation provenance and evidence-covariance accounting."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from .types import EvidenceClass


class ObservationMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observable_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    dataset_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    transform_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    upstream_lineage_id: str = Field(min_length=1)
    evidence_covariance_group_id: str | None = None
    evidence_class: EvidenceClass
    unit: str = Field(min_length=1)
    spatial_scope: str | None = None
    temporal_scope: str | None = None
    notes: str | None = None

    @property
    def conservative_independence_group_id(self) -> str:
        return self.evidence_covariance_group_id or self.upstream_lineage_id


class IndependenceSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_count: int = Field(ge=0)
    independent_group_count: int = Field(ge=0)
    group_ids: tuple[str, ...]


def summarize_independence(mappings: Iterable[ObservationMapping]) -> IndependenceSummary:
    mappings = tuple(mappings)
    observable_ids = [mapping.observable_id for mapping in mappings]
    duplicates = sorted(
        {observable_id for observable_id in observable_ids if observable_ids.count(observable_id) > 1}
    )
    if duplicates:
        raise ValueError("duplicate observable_id(s): " + ", ".join(duplicates))

    groups = tuple(sorted({mapping.conservative_independence_group_id for mapping in mappings}))
    return IndependenceSummary(
        observation_count=len(mappings),
        independent_group_count=len(groups),
        group_ids=groups,
    )
