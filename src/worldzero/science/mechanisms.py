from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from worldzero.science.types import (
    AdmissionDisposition,
    EvidenceClass,
    IdentifiabilityClass,
)


class MechanismAdmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    mechanism_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    evidence_class: EvidenceClass
    identifiability: IdentifiabilityClass
    disposition: AdmissionDisposition
    null_or_rival: str = Field(min_length=1)
    kill_test_id: str | None = None
    holdout_target: str | None = None
    invariant_target: str | None = None
    invariant_required: bool = False
    ablation_expectation: str | None = None
    complexity_dynamic_states: int = Field(default=0, ge=0)
    calibrated_parameter_count: int = Field(default=0, ge=0)
    numerical_integrity: Literal["PASS", "FAIL", "NOT_RUN"] = "NOT_RUN"
    unresolved_negative_transfer_count: int = Field(default=0, ge=0)
    notes: str | None = None


class MechanismRegistry:
    def __init__(self, mechanisms: Iterable[MechanismAdmission] = ()) -> None:
        self._mechanisms: dict[str, MechanismAdmission] = {}
        for mechanism in mechanisms:
            if mechanism.mechanism_id in self._mechanisms:
                raise ValueError(f"duplicate mechanism id: {mechanism.mechanism_id}")
            self._mechanisms[mechanism.mechanism_id] = mechanism

    def get(self, mechanism_id: str) -> MechanismAdmission:
        try:
            return self._mechanisms[mechanism_id]
        except KeyError as exc:
            raise KeyError(f"unknown mechanism id: {mechanism_id}") from exc


def assert_f7_admissible(
    mechanism_ids: Sequence[str],
    registry: MechanismRegistry,
) -> tuple[MechanismAdmission, ...]:
    admitted: list[MechanismAdmission] = []
    for mechanism_id in mechanism_ids:
        mechanism = registry.get(mechanism_id)
        if mechanism.disposition not in {
            AdmissionDisposition.F7_CANDIDATE,
            AdmissionDisposition.F7_ADMITTED,
        }:
            raise ValueError(
                f"mechanism {mechanism_id} disposition is not F7-admissible: "
                f"{mechanism.disposition.value}"
            )
        if not mechanism.invariant_required and mechanism.identifiability not in {
            IdentifiabilityClass.WEAKLY_IDENTIFIABLE,
            IdentifiabilityClass.IDENTIFIABLE_ENOUGH_FOR_TEST,
        }:
            raise ValueError(
                f"mechanism {mechanism_id} fails identifiability gate: "
                f"{mechanism.identifiability.value}"
            )
        if not mechanism.kill_test_id:
            raise ValueError(f"mechanism {mechanism_id} requires a kill test")
        if not mechanism.holdout_target and not mechanism.invariant_target:
            raise ValueError(
                f"mechanism {mechanism_id} requires a holdout or invariant target"
            )
        if mechanism.invariant_required and not mechanism.invariant_target:
            raise ValueError(
                f"mechanism {mechanism_id} invariant exception requires an invariant target"
            )
        if not mechanism.ablation_expectation:
            raise ValueError(f"mechanism {mechanism_id} requires an ablation expectation")
        if mechanism.numerical_integrity != "PASS":
            raise ValueError(
                f"mechanism {mechanism_id} numerical integrity is "
                f"{mechanism.numerical_integrity}, not PASS"
            )
        if mechanism.unresolved_negative_transfer_count:
            raise ValueError(
                f"mechanism {mechanism_id} has unresolved negative-transfer defects"
            )
        admitted.append(mechanism)
    return tuple(admitted)
