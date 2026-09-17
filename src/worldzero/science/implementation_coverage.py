"""Reconcile declared causal topology with executable implementation bindings."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .topology import CausalTopologyV2
from .topology import ImplementationBinding as TopologyImplementationBinding
from .types import ControlMode


class ImplementationBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topology_object_id: str = Field(min_length=1)
    object_kind: Literal["NODE", "RELATION"]
    module: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    behavioral_contract_id: str | None = None
    binding_status: Literal["BOUND", "INTENTIONALLY_EXTERNAL", "UNBOUND"]
    micro_test_ids: tuple[str, ...] = ()


class ImplementationCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["IMPLEMENTATION_COVERAGE_V1"]
    coverage_id: str = Field(min_length=1)
    topology_id: str = Field(min_length=1)
    topology_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    bindings: tuple[ImplementationBinding, ...]
    undeclared_runtime_relations: tuple[str, ...] = ()
    missing_declared_relations: tuple[str, ...] = ()
    coverage_status: Literal["PASS", "FAIL", "INCOMPLETE"]
    notes: str | None = None

    @model_validator(mode="after")
    def reject_obvious_false_pass(self) -> ImplementationCoverage:
        if self.coverage_status == "PASS" and (
            self.undeclared_runtime_relations or self.missing_declared_relations
        ):
            raise ValueError("coverage_status PASS conflicts with declared coverage defects")
        return self


def _binding_index(
    coverage: ImplementationCoverage,
) -> tuple[dict[tuple[str, str], ImplementationBinding], list[str]]:
    index: dict[tuple[str, str], ImplementationBinding] = {}
    defects: list[str] = []
    for binding in coverage.bindings:
        key = (binding.object_kind, binding.topology_object_id)
        if key in index:
            defects.append(
                f"duplicate binding for {binding.object_kind} {binding.topology_object_id}"
            )
        else:
            index[key] = binding
    return index, defects


def validate_coverage(topology: CausalTopologyV2, coverage: ImplementationCoverage) -> None:
    """Fail closed unless coverage exactly reconciles the active declared topology."""
    defects: list[str] = []

    if coverage.topology_id != topology.topology_id:
        defects.append(
            f"topology_id mismatch: coverage={coverage.topology_id} topology={topology.topology_id}"
        )
    expected_digest = topology.digest()
    if coverage.topology_digest != expected_digest:
        defects.append(
            f"topology digest mismatch: coverage={coverage.topology_digest} expected={expected_digest}"
        )

    if coverage.undeclared_runtime_relations:
        defects.append(
            "undeclared runtime relation(s): " + ", ".join(coverage.undeclared_runtime_relations)
        )
    if coverage.missing_declared_relations:
        defects.append(
            "reported missing declared relation(s): " + ", ".join(coverage.missing_declared_relations)
        )

    index, duplicate_defects = _binding_index(coverage)
    defects.extend(duplicate_defects)

    node_by_id = {node.id: node for node in topology.nodes}
    relation_by_id = {relation.id: relation for relation in topology.relations}

    for binding in coverage.bindings:
        declared_binding: TopologyImplementationBinding | None
        if binding.object_kind == "NODE":
            declared_node = node_by_id.get(binding.topology_object_id)
            if declared_node is None:
                defects.append(f"binding targets undeclared NODE {binding.topology_object_id}")
                continue
            declared_binding = declared_node.implementation_binding
        else:
            declared_relation = relation_by_id.get(binding.topology_object_id)
            if declared_relation is None:
                defects.append(f"binding targets undeclared RELATION {binding.topology_object_id}")
                continue
            declared_binding = declared_relation.implementation_binding

        if declared_binding is not None and (
            binding.module != declared_binding.module
            or binding.symbol != declared_binding.symbol
            or binding.behavioral_contract_id != declared_binding.behavioral_contract_id
        ):
            defects.append(
                f"binding drift for {binding.topology_object_id}: "
                f"coverage={binding.module}:{binding.symbol}:{binding.behavioral_contract_id} "
                f"declared={declared_binding.module}:{declared_binding.symbol}:"
                f"{declared_binding.behavioral_contract_id}"
            )

    for relation in topology.relations:
        if relation.control_mode == ControlMode.ABSENT:
            continue
        relation_binding = index.get(("RELATION", relation.id))
        if relation_binding is None:
            defects.append(f"active relation lacks implementation binding: {relation.id}")
            continue
        if relation_binding.binding_status not in {"BOUND", "INTENTIONALLY_EXTERNAL"}:
            defects.append(
                f"active relation is not bound or intentionally external: {relation.id}"
            )
        if relation.control_mode == ControlMode.ENDOGENOUS and not relation_binding.micro_test_ids:
            defects.append(f"endogenous relation lacks micro-test: {relation.id}")

    for node in topology.nodes:
        if node.implementation_binding is None:
            continue
        node_binding = index.get(("NODE", node.id))
        if node_binding is None:
            defects.append(f"declared node implementation lacks coverage binding: {node.id}")
        elif node_binding.binding_status != "BOUND":
            defects.append(f"declared node implementation is not BOUND: {node.id}")

    if coverage.coverage_status != "PASS":
        defects.append(f"coverage_status is not PASS: {coverage.coverage_status}")

    if defects:
        raise ValueError("implementation coverage failed: " + "; ".join(defects))
