from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Set as AbstractSet
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.mechanisms import MechanismRegistry

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
    family_name: str = Field(min_length=1)
    status: FamilyStatus = "DRAFT"
    purpose: str | None = None
    topology_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    enabled_mechanism_ids: tuple[str, ...] = ()
    required_mechanism_ids: tuple[str, ...] = ()
    forbidden_mechanism_ids: tuple[str, ...] = ()
    comparison_observable_ids: tuple[str, ...] = ()
    hostile_control_ids: tuple[str, ...] = ()
    notes: str | None = None

    @model_validator(mode="after")
    def validate_manifest(self) -> ModelFamilyManifest:
        if self.status != "DRAFT" and self.topology_digest is None:
            raise ValueError("topology_digest is required once a family leaves DRAFT")

        for field_name, values in (
            ("enabled_mechanism_ids", self.enabled_mechanism_ids),
            ("required_mechanism_ids", self.required_mechanism_ids),
            ("forbidden_mechanism_ids", self.forbidden_mechanism_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} contains duplicate mechanism ids")

        enabled = set(self.enabled_mechanism_ids)
        required = set(self.required_mechanism_ids)
        forbidden = set(self.forbidden_mechanism_ids)
        if required - enabled:
            missing = ", ".join(sorted(required - enabled))
            raise ValueError(f"required mechanisms must be enabled: {missing}")
        if enabled & forbidden:
            conflict = ", ".join(sorted(enabled & forbidden))
            raise ValueError(f"enabled mechanisms cannot be forbidden: {conflict}")
        return self

    def validate_enabled_mechanisms(
        self,
        enabled_mechanism_ids: AbstractSet[str],
        registry: MechanismRegistry,
    ) -> tuple[str, ...]:
        enabled = set(enabled_mechanism_ids)
        forbidden = enabled & set(self.forbidden_mechanism_ids)
        if forbidden:
            raise ValueError(f"forbidden mechanisms enabled: {', '.join(sorted(forbidden))}")

        missing = set(self.required_mechanism_ids) - enabled
        if missing:
            raise ValueError(f"required mechanisms missing: {', '.join(sorted(missing))}")

        declared = set(self.enabled_mechanism_ids)
        if enabled != declared:
            added = sorted(enabled - declared)
            removed = sorted(declared - enabled)
            raise ValueError(
                "runtime mechanism set differs from family manifest: "
                f"added={added} removed={removed}"
            )

        for mechanism_id in sorted(enabled):
            registry.get(mechanism_id)
        return tuple(sorted(enabled))


class FamilyRegistry:
    def __init__(self, families: Iterable[ModelFamilyManifest] = ()) -> None:
        self._families: dict[str, ModelFamilyManifest] = {}
        for family in families:
            if family.family_id in self._families:
                raise ValueError(f"duplicate family id: {family.family_id}")
            self._families[family.family_id] = family

    def get(self, family_id: str) -> ModelFamilyManifest:
        try:
            return self._families[family_id]
        except KeyError as exc:
            raise KeyError(f"unknown family id: {family_id}") from exc
