from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from worldzero.science.types import EvidenceClass


class SourceRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    locator: str | None = None
    upstream_lineage_id: str | None = None
    notes: str | None = None


class ClaimRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    proposition: str = Field(min_length=1)
    evidence_class: EvidenceClass
    scope: str | None = None
    sources: tuple[SourceRef, ...] = ()
    rival_interpretations: tuple[str, ...] = ()
    model_obligation: str | None = None
    downgrade_condition: str | None = None
    supersedes_revision: int | None = Field(default=None, ge=1)


class ClaimRegistry:
    def __init__(self, records: Iterable[ClaimRecord] = ()) -> None:
        self._records: dict[tuple[str, int], ClaimRecord] = {}
        for record in records:
            self.add(record)

    def add(self, record: ClaimRecord) -> ClaimRecord:
        key = (record.claim_id, record.revision)
        if key in self._records:
            raise ValueError(f"duplicate claim revision: {record.claim_id}@{record.revision}")
        if record.supersedes_revision is not None:
            superseded_key = (record.claim_id, record.supersedes_revision)
            if superseded_key not in self._records:
                raise ValueError(
                    "supersedes revision does not exist: "
                    f"{record.claim_id}@{record.supersedes_revision}"
                )
        self._records[key] = record
        return record

    def get(self, claim_id: str, revision: int) -> ClaimRecord:
        return self._records[(claim_id, revision)]

    def current(self, claim_id: str) -> ClaimRecord:
        matching = [
            record
            for (stored_claim_id, _), record in self._records.items()
            if stored_claim_id == claim_id
        ]
        if not matching:
            raise KeyError(claim_id)
        return max(matching, key=lambda record: record.revision)
