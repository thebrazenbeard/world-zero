"""Topology-to-executable implementation coverage contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import content_digest
from .topology import CausalTopologyV2
from .types import ControlMode


class ImplementationBindingRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    topology_object_id: str = Field(min_length=1)
    object_kind: Literal["NODE", "RELATION"]
    module: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    behavioral_contract_id: str | None = None
    binding_status: Literal["BOUND", "INTENTIONALLY_EXTERNAL", "UNBOUND"]
    micro_test_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_relation_micro_test(self) -> ImplementationBindingRecord:
        if self.object_kind == "RELATION" and self.binding_status == "BOUND" and not self.micro_test_ids:
            raise ValueError("BOUND relation requires at least one behavioral micro test")
        return self


class ImplementationCoverageV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["IMPLEMENTATION_COVERAGE_V1"]
    coverage_id: str = Field(min_length=1)
    topology_id: str = Field(min_length=1)
    topology_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    bindings: tuple[ImplementationBindingRecord, ...] = ()
    undeclared_runtime_relations: tuple[str, ...] = ()
    missing_declared_relations: tuple[str, ...] = ()
    coverage_status: Literal["PASS", "FAIL", "INCOMPLETE"]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_coverage(self) -> ImplementationCoverageV1:
        keys = [(binding.object_kind, binding.topology_object_id) for binding in self.bindings]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate binding for topology object")

        if self.coverage_status != "PASS":
            return self
        if self.undeclared_runtime_relations:
            raise ValueError("PASS requires empty undeclared_runtime_relations")
        if self.missing_declared_relations:
            raise ValueError("PASS requires empty missing_declared_relations")
        unbound = [
            binding.topology_object_id
            for binding in self.bindings
            if binding.binding_status == "UNBOUND"
        ]
        if unbound:
            raise ValueError(f"PASS cannot contain UNBOUND bindings: {unbound}")
        return self

    def digest(self) -> str:
        return content_digest(self)

def validate_coverage(topology: CausalTopologyV2, coverage: ImplementationCoverageV1) -> None:
    """Fail closed unless coverage exactly reconciles with the declared topology."""
    if coverage.topology_id != topology.topology_id:
        raise ValueError(
            f"coverage topology_id {coverage.topology_id} does not match {topology.topology_id}"
        )
    expected_digest = topology.digest()
    if coverage.topology_digest != expected_digest:
        raise ValueError("coverage topology_digest does not match exact topology content")

    node_ids = {node.id for node in topology.nodes}
    relation_by_id = {relation.id: relation for relation in topology.relations}
    relation_ids = set(relation_by_id)
    node_bindings: dict[str, ImplementationBindingRecord] = {}
    relation_bindings: dict[str, ImplementationBindingRecord] = {}

    for binding in coverage.bindings:
        if binding.object_kind == "NODE":
            if binding.topology_object_id not in node_ids:
                raise ValueError(f"binding references undeclared node {binding.topology_object_id}")
            node_bindings[binding.topology_object_id] = binding
        else:
            if binding.topology_object_id not in relation_ids:
                raise ValueError(f"binding references undeclared relation {binding.topology_object_id}")
            relation_bindings[binding.topology_object_id] = binding

    active_relations = {
        relation.id
        for relation in topology.relations
        if relation.control_mode != ControlMode.ABSENT
    }
    missing_active = sorted(active_relations - relation_bindings.keys())
    if missing_active:
        raise ValueError(f"missing active relation bindings: {', '.join(missing_active)}")

    declared_node_bindings = {
        node.id for node in topology.nodes if node.implementation_binding is not None
    }
    missing_nodes = sorted(declared_node_bindings - node_bindings.keys())
    if missing_nodes:
        raise ValueError(f"missing declared node bindings: {', '.join(missing_nodes)}")

    for node in topology.nodes:
        declared = node.implementation_binding
        if declared is None:
            continue
        actual = node_bindings[node.id]
        if (
            actual.module != declared.module
            or actual.symbol != declared.symbol
            or actual.behavioral_contract_id != declared.behavioral_contract_id
        ):
            raise ValueError(f"node {node.id} differs from declared implementation binding")

    for relation in topology.relations:
        declared = relation.implementation_binding
        if declared is None or relation.id not in relation_bindings:
            continue
        actual = relation_bindings[relation.id]
        if (
            actual.module != declared.module
            or actual.symbol != declared.symbol
            or actual.behavioral_contract_id != declared.behavioral_contract_id
        ):
            raise ValueError(
                f"relation {relation.id} differs from declared implementation binding"
            )

    for relation_id in active_relations:
        relation = relation_by_id[relation_id]
        binding = relation_bindings[relation_id]
        if binding.binding_status == "UNBOUND":
            raise ValueError(f"active relation {relation_id} is UNBOUND")
        if relation.control_mode == ControlMode.ENDOGENOUS and not binding.micro_test_ids:
            raise ValueError(f"endogenous relation {relation_id} requires behavioral micro tests")

ImplementationBinding = ImplementationBindingRecord
ImplementationCoverage = ImplementationCoverageV1
