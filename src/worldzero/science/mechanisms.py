"""Mechanism admission and F7 composition gates."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .types import AdmissionDisposition, EvidenceClass, IdentifiabilityClass


class ComplexityCost(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dynamic_states: int = Field(default=0, ge=0)
    calibrated_parameters: int = Field(default=0, ge=0)
    lookup_functions: int = Field(default=0, ge=0)
    latent_variables: int = Field(default=0, ge=0)
    external_scenario_inputs: int = Field(default=0, ge=0)
    runtime_cost_class: Literal["TRIVIAL", "LOW", "MODERATE", "HIGH", "EXTREME"] = "LOW"


class MechanismAdmission(BaseModel):
    """Evidence packet for one proposed causal/accounting mechanism."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mechanism_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    affected_object_ids: tuple[str, ...] = Field(min_length=1)
    interpretation: str = Field(min_length=1)
    units_and_conservation: str = Field(min_length=1)
    evidence_class: EvidenceClass
    clarity_pass: bool
    source_ids: tuple[str, ...] = ()
    rival_or_null: str = Field(min_length=1)
    uncertainty: str = Field(min_length=1)
    identifiability: IdentifiabilityClass
    motivating_residual: str | None = None
    kill_test_id: str | None = None
    kill_test_survived: bool = False
    holdout_target: str | None = None
    invariant_target: str | None = None
    hard_invariant_required: bool = False
    holdout_or_invariant_value_pass: bool = False
    ablation_expectation: str | None = None
    ablation_value_pass: bool = False
    structural_rival_analysis: str | None = None
    complexity: ComplexityCost
    complexity_proportionate: bool
    numerical_integrity: Literal["PASS", "FAIL", "UNKNOWN"]
    unresolved_negative_transfer_defects: tuple[str, ...] = ()
    disposition: AdmissionDisposition
    computational_notes: str | None = None


class MechanismRegistry:
    def __init__(self, mechanisms: Iterable[MechanismAdmission] = ()) -> None:
        self._by_id: dict[str, MechanismAdmission] = {}
        for mechanism in mechanisms:
            if mechanism.mechanism_id in self._by_id:
                raise ValueError(f"duplicate mechanism_id: {mechanism.mechanism_id}")
            self._by_id[mechanism.mechanism_id] = mechanism

    def get(self, mechanism_id: str) -> MechanismAdmission:
        try:
            return self._by_id[mechanism_id]
        except KeyError as exc:
            raise KeyError(f"unknown mechanism_id: {mechanism_id}") from exc


def _f7_defects(mechanism: MechanismAdmission) -> list[str]:
    defects: list[str] = []

    if not mechanism.clarity_pass:
        defects.append("semantic/boundary clarity gate did not pass")

    ordinarily_identifiable = mechanism.identifiability in {
        IdentifiabilityClass.IDENTIFIABLE_ENOUGH_FOR_TEST,
        IdentifiabilityClass.WEAKLY_IDENTIFIABLE,
    }
    if not ordinarily_identifiable:
        if not mechanism.hard_invariant_required:
            defects.append(
                "identifiability is below WEAKLY_IDENTIFIABLE without a hard-invariant exception"
            )
        elif not mechanism.invariant_target:
            defects.append("hard-invariant identifiability exception lacks an explicit invariant target")

    if not mechanism.kill_test_id:
        defects.append("preregistered kill test is missing")
    elif not mechanism.kill_test_survived:
        defects.append("preregistered kill test has not been survived")

    if not (mechanism.holdout_target or mechanism.invariant_target):
        defects.append("holdout or invariant target is missing")
    if not mechanism.holdout_or_invariant_value_pass:
        defects.append("claim-relevant holdout/invariant value has not passed")

    if not mechanism.ablation_expectation:
        defects.append("ablation expectation is missing")
    if not mechanism.ablation_value_pass:
        defects.append("nontrivial ablation value has not passed")

    if not mechanism.structural_rival_analysis:
        defects.append("structural rival analysis is missing")

    if not mechanism.complexity_proportionate:
        defects.append("complexity cost is not proportionate to demonstrated gain")

    if mechanism.numerical_integrity != "PASS":
        defects.append(f"numerical integrity is not PASS: {mechanism.numerical_integrity}")

    if mechanism.unresolved_negative_transfer_defects:
        defects.append(
            "unresolved negative-transfer defect(s): "
            + ", ".join(mechanism.unresolved_negative_transfer_defects)
        )

    if mechanism.disposition not in {
        AdmissionDisposition.F7_CANDIDATE,
        AdmissionDisposition.F7_ADMITTED,
    }:
        defects.append(f"disposition is not F7-eligible: {mechanism.disposition.value}")

    return defects


def assert_f7_admissible(
    mechanism_ids: Iterable[str], registry: MechanismRegistry
) -> None:
    """Fail closed unless every selected mechanism satisfies the full F7 promotion gate."""

    seen: set[str] = set()
    failures: list[str] = []
    for mechanism_id in mechanism_ids:
        if mechanism_id in seen:
            failures.append(f"duplicate mechanism requested for F7 composition: {mechanism_id}")
            continue
        seen.add(mechanism_id)
        mechanism = registry.get(mechanism_id)
        defects = _f7_defects(mechanism)
        if defects:
            failures.append(f"{mechanism_id}: " + "; ".join(defects))

    if failures:
        raise ValueError("F7 admission failed: " + " | ".join(failures))
