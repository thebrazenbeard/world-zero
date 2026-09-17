"""Upstream evidence-lineage grouping for correlated derived sources."""

from __future__ import annotations

from collections.abc import Iterable, Set

from pydantic import BaseModel, ConfigDict, Field


class LineageRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str = Field(min_length=1)
    upstream_lineage_id: str = Field(min_length=1)
    derivation_kind: str | None = None
    parent_source_ids: tuple[str, ...] = ()


class LineageRegistry:
    def __init__(self, refs: Iterable[LineageRef] = ()) -> None:
        self._by_source: dict[str, LineageRef] = {}
        for ref in refs:
            if ref.source_id in self._by_source:
                raise ValueError(f"duplicate lineage source_id: {ref.source_id}")
            self._by_source[ref.source_id] = ref

    def get(self, source_id: str) -> LineageRef:
        return self._by_source[source_id]

    def independent_source_count(self, source_ids: Set[str] | set[str]) -> int:
        unknown = sorted(source_ids.difference(self._by_source))
        if unknown:
            raise KeyError(f"unknown lineage source IDs: {', '.join(unknown)}")
        return len({self._by_source[source_id].upstream_lineage_id for source_id in source_ids})
