"""Append-oriented scientific claims and source references."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .types import EvidenceClass


class SourceRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str = Field(min_length=1)
    locator: str | None = None


class ClaimRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    proposition: str = Field(min_length=1)
    evidence_class: EvidenceClass
    scope: str | None = None
    sources: tuple[SourceRef, ...] = ()
    rivals: tuple[str, ...] = ()
    model_obligation: str | None = None
    downgrade_condition: str | None = None
    supersedes_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def supersession_precedes_revision(self) -> ClaimRecord:
        if self.supersedes_revision is not None and self.supersedes_revision >= self.revision:
            raise ValueError("supersedes_revision must precede revision")
        return self


class ClaimRegistry:
    """Preserve every claim revision while exposing the current revision."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, int], ClaimRecord] = {}

    def add(self, record: ClaimRecord) -> None:
        key = (record.claim_id, record.revision)
        if key in self._records:
            raise ValueError(f"duplicate claim revision: {record.claim_id}@{record.revision}")
        if record.supersedes_revision is not None:
            prior_key = (record.claim_id, record.supersedes_revision)
            if prior_key not in self._records:
                raise ValueError(
                    f"supersedes missing revision: {record.claim_id}@{record.supersedes_revision}"
                )
        self._records[key] = record

    def get(self, claim_id: str, revision: int) -> ClaimRecord:
        return self._records[(claim_id, revision)]

    def current(self, claim_id: str) -> ClaimRecord:
        revisions = [
            revision
            for record_id, revision in self._records
            if record_id == claim_id
        ]
        if not revisions:
            raise KeyError(claim_id)
        return self._records[(claim_id, max(revisions))]
