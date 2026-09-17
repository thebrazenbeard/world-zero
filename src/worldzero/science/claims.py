"""Append-oriented scientific claims and exact source references."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .types import EvidenceClass


class SourceRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str = Field(min_length=1)
    locator: str | None = None
    title: str | None = None
    doi: str | None = None
    url: str | None = None


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
    def validate_supersession_direction(self) -> ClaimRecord:
        if self.supersedes_revision is not None and self.supersedes_revision >= self.revision:
            raise ValueError("supersedes_revision must be lower than revision")
        return self


class ClaimRegistry:
    """In-memory append-oriented registry; revisions are never overwritten."""

    def __init__(self, claims: Iterable[ClaimRecord] = ()) -> None:
        self._claims: dict[tuple[str, int], ClaimRecord] = {}
        for claim in claims:
            self.add(claim)

    def add(self, claim: ClaimRecord) -> None:
        key = (claim.claim_id, claim.revision)
        if key in self._claims:
            raise ValueError(f"duplicate claim revision: {claim.claim_id}@{claim.revision}")
        if claim.supersedes_revision is not None:
            superseded_key = (claim.claim_id, claim.supersedes_revision)
            if superseded_key not in self._claims:
                raise ValueError(
                    "superseded revision is missing: "
                    f"{claim.claim_id}@{claim.supersedes_revision}"
                )
        self._claims[key] = claim

    def get(self, claim_id: str, revision: int) -> ClaimRecord:
        return self._claims[(claim_id, revision)]

    def current(self, claim_id: str) -> ClaimRecord:
        revisions = [rev for cid, rev in self._claims if cid == claim_id]
        if not revisions:
            raise KeyError(claim_id)
        return self._claims[(claim_id, max(revisions))]
