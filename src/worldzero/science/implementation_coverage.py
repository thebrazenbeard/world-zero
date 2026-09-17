from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.topology import CausalTopologyV2
from worldzero.science.types import ControlMode


class ImplementationBinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    topology_object_id: str = Field(min_length=1)
    object_kind: Literal["NODE", "RELATION"]
    module: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    behavioral_contract_id: str | None = None
    binding_status: Literal["BOUND", "INTENTIONALLY_EXTERNAL", "UNBOUND"]
    micro_test_ids: tuple[str, ...] = ()


class ImplementationCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["IMPLEMENTATION_COVERAGE_V1"]
    coverage_id: str = Field(min_length=1)
    topology_id: str = Field(min_length=1)
    topology_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    bindings: tuple[ImplementationBinding, ...] = ()
    undeclared_runtime_relations: tuple[str, ...] = ()
    missing_declared_relations: tuple[str, ...] = ()
    coverage_status: Literal["PASS", "FAIL", "INCOMPLETE"]
    notes: str | None = None

    @model_validator(mode="after")
    def pass_requires_clean_coverage(self) -> ImplementationCoverage:
        if self.coverage_status == "PASS":
            if self.undeclared_runtime_relations:
                raise ValueError("PASS coverage cannot contain undeclared runtime relations")
            if self.missing_declared_relations:
                raise ValueError("PASS coverage cannot contain missing declared relations")
        return self


def validate_coverage(
    topology: CausalTopologyV2,
    coverage: ImplementationCoverage,
) -> ImplementationCoverage:
    if coverage.topology_id != topology.topology_id:
        raise ValueError(
            f"topology id mismatch: coverage={coverage.topology_id} topology={topology.topology_id}"
        )
    if coverage.topology_digest != topology.digest():
        raise ValueError("topology digest mismatch")

    relation_bindings = {
        binding.topology_object_id: binding
        for binding in coverage.bindings
        if binding.object_kind == "RELATION"
    }
    required_relations = {
        relation.id
        for relation in topology.relations
        if relation.control_mode != ControlMode.ABSENT
    }

    missing = sorted(required_relations - relation_bindings.keys())
    if missing:
        raise ValueError(f"missing declared relation bindings: {', '.join(missing)}")

    for relation in topology.relations:
        if relation.id not in required_relations:
            continue
        binding = relation_bindings[relation.id]
        if binding.binding_status == "UNBOUND":
            raise ValueError(f"relation {relation.id} is UNBOUND")
        if (
            relation.control_mode == ControlMode.ENDOGENOUS
            and binding.binding_status == "BOUND"
            and not binding.micro_test_ids
        ):
            raise ValueError(f"endogenous relation {relation.id} requires a micro-test")

    if coverage.undeclared_runtime_relations:
        raise ValueError(
            "undeclared runtime relations: "
            + ", ".join(sorted(coverage.undeclared_runtime_relations))
        )
    if coverage.missing_declared_relations:
        raise ValueError(
            "coverage records missing declared relations: "
            + ", ".join(sorted(coverage.missing_declared_relations))
        )
    if coverage.coverage_status != "PASS":
        raise ValueError(f"coverage status is not PASS: {coverage.coverage_status}")
    return coverage
