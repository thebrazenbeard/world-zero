"""Higher-order causal topology contracts for World Zero."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import content_digest
from .types import ControlMode, EvidenceClass

ID_PATTERN = r"^[A-Z0-9_]+$"
_ID_RE = re.compile(ID_PATTERN)

ModelFamily = Literal[
    "F0_WORLD3_CONTROL",
    "F1_MARKET_ADAPTIVE",
    "F2_ENDOGENOUS_INNOVATION",
    "F3_NET_ENERGY_MATERIAL",
    "F4_INSTITUTIONAL_FRAGILITY",
    "F5_RESILIENT_REGIONAL",
    "F6_COMPOUND_RISK",
    "F7_MINIMAL_ADAPTIVE_SYNTHESIS",
]
MODEL_FAMILIES = {
    "F0_WORLD3_CONTROL",
    "F1_MARKET_ADAPTIVE",
    "F2_ENDOGENOUS_INNOVATION",
    "F3_NET_ENERGY_MATERIAL",
    "F4_INSTITUTIONAL_FRAGILITY",
    "F5_RESILIENT_REGIONAL",
    "F6_COMPOUND_RISK",
    "F7_MINIMAL_ADAPTIVE_SYNTHESIS",
}

TopologyStatus = Literal[
    "DRAFT",
    "FROZEN_CANDIDATE",
    "UNDER_TEST",
    "QUALIFIED_WITHIN_SCOPE",
    "REJECTED",
    "SUPERSEDED",
]
SpatialScope = Literal["GLOBAL", "REGIONAL", "BILATERAL_NETWORK", "LOCAL_AGGREGATED"]
NodeKind = Literal[
    "STOCK",
    "FLOW",
    "AUXILIARY",
    "OBSERVATION",
    "POLICY",
    "SHOCK",
    "THRESHOLD_STATE",
    "NETWORK_STATE",
    "PRICE",
    "TECHNOLOGY_STATE",
]
UncertaintyKind = Literal[
    "PARAMETER",
    "MEASUREMENT",
    "STRUCTURAL",
    "SCENARIO",
    "DEEP_UNCERTAINTY",
    "NONE_DECLARED",
]
RelationType = Literal[
    "CAUSES",
    "CONSTRAINS",
    "ALLOCATES",
    "OBSERVES",
    "MODULATES",
    "SUBSTITUTES",
    "ENABLES",
    "DAMAGES",
    "DEPLETES",
    "REPLENISHES",
    "TRANSMITS",
    "TRIGGERS",
    "PRICES",
    "LEARNED_RESPONSE",
    "JOINT_RESPONSE",
]
FunctionalFormClass = Literal[
    "LINEAR",
    "NONLINEAR",
    "LOOKUP",
    "THRESHOLD",
    "ALLOCATION",
    "DELAY",
    "NETWORK",
    "STOCHASTIC",
    "CUSTOM",
    "UNKNOWN",
]
Polarity = Literal["POSITIVE", "NEGATIVE", "MIXED", "NON_MONOTONIC", "CONDITIONAL", "UNKNOWN"]
HoldoutClass = Literal["TEMPORAL", "REGIONAL", "VARIABLE", "STRUCTURAL", "SHOCK", "NEGATIVE_CONTROL"]
ConflictStatus = Literal["OPEN", "RESOLVED", "SUPERSEDED", "UNRESOLVED_BY_DATA"]


class Scope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial: SpatialScope
    regions: tuple[str, ...] = ()
    time_start: float | None = None
    time_end: float | None = None


class TopologySourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    evidence_class: EvidenceClass
    locator: str | None = None
    claim_id: str | None = None
    upstream_lineage_id: str | None = None
    notes: str | None = None


class Uncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: UncertaintyKind
    distribution: str | None = None
    range: tuple[float, float] | None = None
    notes: str | None = None


class ImplementationBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    behavioral_contract_id: str | None = None


class TopologyNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=ID_PATTERN)
    label: str | None = None
    kind: NodeKind
    control_mode: ControlMode
    evidence_class: EvidenceClass
    units: str | None = None
    scope: Scope
    conservation_group: str | None = None
    observation_mapping: str | None = None
    uncertainty: Uncertainty | None = None
    sources: tuple[TopologySourceRef, ...] = ()
    implementation_binding: ImplementationBinding | None = None
    notes: str | None = None


class TopologyRelation(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(pattern=ID_PATTERN)
    inputs: tuple[str, ...] = Field(min_length=1)
    outputs: tuple[str, ...] = Field(min_length=1)
    relation_type: RelationType
    functional_form_class: FunctionalFormClass
    polarity: Polarity
    evidence_class: EvidenceClass
    control_mode: ControlMode
    lag_model: str | None = None
    equation_ref: str | None = None
    scope: Scope
    uncertainty: Uncertainty
    sources: tuple[TopologySourceRef, ...] = ()
    rival_relation_ids: tuple[str, ...] = ()
    kill_test_ids: tuple[str, ...] = ()
    implementation_binding: ImplementationBinding | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_relation_ids(self) -> "TopologyRelation":
        for field_name, values in (("inputs", self.inputs), ("outputs", self.outputs)):
            if len(values) != len(set(values)):
                raise ValueError(f"{self.id} has duplicate {field_name}")
            invalid = [value for value in values if not _ID_RE.fullmatch(value)]
            if invalid:
                raise ValueError(f"{self.id} has invalid {field_name}: {invalid}")
        return self


class KillTest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=ID_PATTERN)
    claim_or_mechanism: str
    test: str
    minimum_evidence: str | None = None
    failure_meaning: str
    holdout_class: HoldoutClass | None = None


class TopologyConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    status: ConflictStatus
    rival_claims: tuple[str, ...] = ()
    resolution_basis: str | None = None


class CausalTopologyV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["CAUSAL_TOPOLOGY_V2"]
    topology_id: str = Field(min_length=1)
    model_family: ModelFamily
    status: TopologyStatus | None = None
    description: str | None = None
    region_definition_id: str | None = None
    provenance_refs: tuple[str, ...] = ()
    nodes: tuple[TopologyNode, ...] = Field(min_length=1)
    relations: tuple[TopologyRelation, ...]
    kill_tests: tuple[KillTest, ...] = Field(min_length=1)
    known_conflicts: tuple[TopologyConflict, ...] = ()

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "CausalTopologyV2":
        node_ids = [node.id for node in self.nodes]
        duplicate_nodes = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
        if duplicate_nodes:
            raise ValueError(f"duplicate node ID(s): {', '.join(duplicate_nodes)}")

        relation_ids = [relation.id for relation in self.relations]
        duplicate_relations = sorted(
            {relation_id for relation_id in relation_ids if relation_ids.count(relation_id) > 1}
        )
        if duplicate_relations:
            raise ValueError(f"duplicate relation ID(s): {', '.join(duplicate_relations)}")

        kill_test_ids = [kill_test.id for kill_test in self.kill_tests]
        duplicate_kill_tests = sorted(
            {kill_id for kill_id in kill_test_ids if kill_test_ids.count(kill_id) > 1}
        )
        if duplicate_kill_tests:
            raise ValueError(f"duplicate kill-test ID(s): {', '.join(duplicate_kill_tests)}")

        node_set = set(node_ids)
        relation_set = set(relation_ids)
        kill_test_set = set(kill_test_ids)

        for relation in self.relations:
            missing_nodes = sorted((set(relation.inputs) | set(relation.outputs)) - node_set)
            if missing_nodes:
                raise ValueError(
                    f"relation {relation.id} references missing node(s): {', '.join(missing_nodes)}"
                )

            missing_kill_tests = sorted(set(relation.kill_test_ids) - kill_test_set)
            if missing_kill_tests:
                raise ValueError(
                    f"relation {relation.id} references missing kill test(s): "
                    f"{', '.join(missing_kill_tests)}"
                )

            for rival in relation.rival_relation_ids:
                if ":" in rival:
                    family_id, external_relation_id = rival.split(":", 1)
                    if family_id not in MODEL_FAMILIES or not _ID_RE.fullmatch(external_relation_id):
                        raise ValueError(
                            f"relation {relation.id} has malformed external rival: {rival}"
                        )
                elif rival not in relation_set:
                    raise ValueError(
                        f"relation {relation.id} references missing local rival relation: {rival}"
                    )

        return self

    def digest(self) -> str:
        return content_digest(self)
