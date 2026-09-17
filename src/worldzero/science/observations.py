from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from worldzero.science.types import EvidenceClass


class ObservationMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observable_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    dataset_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    transform_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    upstream_lineage_id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    unit: str = Field(min_length=1)
    covariance_group: str | None = None


class IndependenceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    observation_count: int = Field(ge=0)
    independent_group_count: int = Field(ge=0)
    shared_group_ids: tuple[str, ...] = ()


def summarize_independence(
    observations: Iterable[ObservationMapping],
) -> IndependenceSummary:
    items = tuple(observations)
    if not items:
        return IndependenceSummary(observation_count=0, independent_group_count=0)

    parent = list(range(len(items)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    lineage_owner: dict[str, int] = {}
    covariance_owner: dict[str, int] = {}
    lineage_counts = Counter(item.upstream_lineage_id for item in items)
    covariance_counts = Counter(
        item.covariance_group for item in items if item.covariance_group is not None
    )

    for index, item in enumerate(items):
        prior_lineage = lineage_owner.setdefault(item.upstream_lineage_id, index)
        union(index, prior_lineage)
        if item.covariance_group is not None:
            prior_covariance = covariance_owner.setdefault(item.covariance_group, index)
            union(index, prior_covariance)

    roots = {find(index) for index in range(len(items))}
    shared = {
        group_id for group_id, count in lineage_counts.items() if count > 1
    } | {
        group_id for group_id, count in covariance_counts.items() if count > 1
    }
    return IndependenceSummary(
        observation_count=len(items),
        independent_group_count=len(roots),
        shared_group_ids=tuple(sorted(shared)),
    )
