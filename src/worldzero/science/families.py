"""Causal model-family manifests and family-level mechanism constraints."""

from __future__ import annotations

from collections.abc import Iterable, Set
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FamilyId = Literal[
    "F0_WORLD3_CONTROL",
    "F1_MARKET_ADAPTIVE",
    "F2_ENDOGENOUS_INNOVATION",
    "F3_NET_ENERGY_MATERIAL",
    "F4_INSTITUTIONAL_FRAGILITY",
    "F5_RESILIENT_REGIONAL",
    "F6_COMPOUND_RISK",
    "F7_MINIMAL_ADAPTIVE_SYNTHESIS",
]
FamilyStatus = Literal[
    "DRAFT",
    "FROZEN_CANDIDATE",
    "UNDER_TEST",
    "QUALIFIED_WITHIN_SCOPE",
    "REJECTED",
    "SUPERSEDED",
]


class ModelFamilyManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["MODEL_FAMILY_V1"]
    family_id: FamilyId
    status: FamilyStatus = "DRAFT"
    causal_interpretation: Literal[True] = True
    source_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    topology_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    required_mechanisms: tuple[str, ...] = ()
    forbidden_mechanisms: tuple[str, ...] = ()
    enabled_mechanisms: tuple[str, ...] = ()
    declared_weaknesses: tuple[str, ...] = ()
    hostile_controls: tuple[str, ...] = ()
    notes: str | None = None

    @model_validator(mode="after")
    def validate_family_contract(self) -> "ModelFamilyManifest":
        overlap = sorted(set(self.required_mechanisms) & set(self.forbidden_mechanisms))
        if overlap:
            raise ValueError("mechanisms cannot be both required and forbidden: " + ", ".join(overlap))

        if self.status != "DRAFT":
            if self.source_commit is None:
                raise ValueError("non-DRAFT family requires source_commit")
            if self.topology_digest is None:
                raise ValueError("non-DRAFT family requires topology_digest")

        if self.enabled_mechanisms:
            self.validate_enabled_mechanisms(set(self.enabled_mechanisms))
        return self

    def validate_enabled_mechanisms(self, enabled: Set[str] | set[str]) -> None:
        forbidden = sorted(set(enabled) & set(self.forbidden_mechanisms))
        if forbidden:
            raise ValueError(
                f"{self.family_id} enables forbidden mechanism(s): {', '.join(forbidden)}"
            )
        missing = sorted(set(self.required_mechanisms) - set(enabled))
        if missing:
            raise ValueError(
                f"{self.family_id} is missing required mechanism(s): {', '.join(missing)}"
            )


class FamilyRegistry:
    def __init__(self, manifests: Iterable[ModelFamilyManifest] = ()) -> None:
        self._by_id: dict[str, ModelFamilyManifest] = {}
        for manifest in manifests:
            if manifest.family_id in self._by_id:
                raise ValueError(f"duplicate family_id: {manifest.family_id}")
            self._by_id[manifest.family_id] = manifest

    def get(self, family_id: str) -> ModelFamilyManifest:
        try:
            return self._by_id[family_id]
        except KeyError as exc:
            raise KeyError(f"unknown family_id: {family_id}") from exc
