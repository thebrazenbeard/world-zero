from __future__ import annotations

from collections.abc import Iterable, Set as AbstractSet

from pydantic import BaseModel, ConfigDict, Field


class LineageRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    upstream_lineage_id: str = Field(min_length=1)
    derivation_kind: str | None = None
    parent_source_ids: tuple[str, ...] = ()


class LineageRegistry:
    def __init__(self, refs: Iterable[LineageRef] = ()) -> None:
        self._refs: dict[str, LineageRef] = {}
        for ref in refs:
            if ref.source_id in self._refs:
                raise ValueError(f"duplicate source lineage: {ref.source_id}")
            self._refs[ref.source_id] = ref

    def get(self, source_id: str) -> LineageRef:
        try:
            return self._refs[source_id]
        except KeyError as exc:
            raise KeyError(f"unknown source id: {source_id}") from exc

    def independent_source_count(self, source_ids: AbstractSet[str]) -> int:
        return len({self.get(source_id).upstream_lineage_id for source_id in source_ids})
