"""Hyperedge-capable causal topology contracts for World Zero."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import content_digest
from .types import ControlMode, EvidenceClass

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


class Scope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial: Literal["GLOBAL", "REGIONAL", "BILATERAL_NETWORK", "LOCAL_AGGREGATED"]
    regions: tuple[str, ...] = ()
    time_start: float | None = None
    time_end: float | None = None


class TopologySourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    evidence_class: EvidenceClass
    locator: str | None = None
    claim_id: str | None = None
    upstream_lineage_id: str | None = None
    notes: str | None = None


class Uncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "PARAMETER", "MEASUREMENT", "STRUCTURAL", "SCENARIO",
        "DEEP_UNCERTAINTY", "NONE_DECLARED",
    ]
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

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    label: str | None = None
    kind: Literal[
        "STOCK", "FLOW", "AUXILIARY", "OBSERVATION", "POLICY", "SHOCK",
        "THRESHOLD_STATE", "NETWORK_STATE", "PRICE", "TECHNOLOGY_STATE",
    ]
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
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    inputs: tuple[str, ...] = Field(min_length=1)
    outputs: tuple[str, ...] = Field(min_length=1)
    relation_type: Literal[
        "CAUSES", "CONSTRAINS", "ALLOCATES", "OBSERVES", "MODULATES",
        "SUBSTITUTES", "ENABLES", "DAMAGES", "DEPLETES", "REPLENISHES",
        "TRANSMITS", "TRIGGERS", "PRICES", "LEARNED_RESPONSE", "JOINT_RESPONSE",
    ]
    functional_form_class: Literal[
        "LINEAR", "NONLINEAR", "LOOKUP", "THRESHOLD", "ALLOCATION",
        "DELAY", "NETWORK", "STOCHASTIC", "CUSTOM", "UNKNOWN",
    ]
    polarity: Literal[
        "POSITIVE", "NEGATIVE", "MIXED", "NON_MONOTONIC", "CONDITIONAL", "UNKNOWN",
    ]
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

    @field_validator("inputs", "outputs")
    @classmethod
    def unique_node_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("relation inputs/outputs must be unique")
        return value


class KillTest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    claim_or_mechanism: str
    test: str
    minimum_evidence: str | None = None
    failure_meaning: str
    holdout_class: Literal[
        "TEMPORAL", "REGIONAL", "VARIABLE", "STRUCTURAL", "SHOCK", "NEGATIVE_CONTROL"
    ] | None = None


class TopologyConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    status: Literal["OPEN", "RESOLVED", "SUPERSEDED", "UNRESOLVED_BY_DATA"]
    rival_claims: tuple[str, ...] = ()
    resolution_basis: str | None = None


class CausalTopologyV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["CAUSAL_TOPOLOGY_V2"]
    topology_id: str = Field(min_length=1)
    model_family: ModelFamily
    status: Literal[
        "DRAFT", "FROZEN_CANDIDATE", "UNDER_TEST",
        "QUALIFIED_WITHIN_SCOPE", "REJECTED", "SUPERSEDED",
    ] = "DRAFT"
    description: str | None = None
    region_definition_id: str | None = None
    provenance_refs: tuple[str, ...] = ()
    nodes: tuple[TopologyNode, ...] = Field(min_length=1)
    relations: tuple[TopologyRelation, ...] = ()
    kill_tests: tuple[KillTest, ...] = Field(min_length=1)
    known_conflicts: tuple[TopologyConflict, ...] = ()

    @model_validator(mode="after")
    def validate_references(self) -> CausalTopologyV2:
        node_ids = [node.id for node in self.nodes]
        relation_ids = [relation.id for relation in self.relations]
        kill_test_ids = [test.id for test in self.kill_tests]

        self._require_unique(node_ids, "node")
        self._require_unique(relation_ids, "relation")
        self._require_unique(kill_test_ids, "kill test")

        node_set = set(node_ids)
        relation_set = set(relation_ids)
        kill_test_set = set(kill_test_ids)

        for relation in self.relations:
            self._validate_relation_refs(relation, node_set, relation_set, kill_test_set)
        return self

    @staticmethod
    def _require_unique(values: list[str], kind: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                raise ValueError(f"duplicate {kind} id: {value}")
            seen.add(value)

    @staticmethod
    def _validate_relation_refs(
        relation: TopologyRelation,
        node_ids: set[str],
        relation_ids: set[str],
        kill_test_ids: set[str],
    ) -> None:
        for node_id in (*relation.inputs, *relation.outputs):
            if node_id not in node_ids:
                raise ValueError(f"relation {relation.id} references missing node {node_id}")
        for kill_test_id in relation.kill_test_ids:
            if kill_test_id not in kill_test_ids:
                raise ValueError(
                    f"relation {relation.id} references missing kill test {kill_test_id}"
                )
        for rival_id in relation.rival_relation_ids:
            if ":" in rival_id:
                family_id, external_relation_id = rival_id.split(":", maxsplit=1)
                if not family_id or not external_relation_id:
                    raise ValueError(f"malformed external rival relation: {rival_id}")
            elif rival_id not in relation_ids:
                raise ValueError(f"relation {relation.id} references missing rival {rival_id}")

    def digest(self) -> str:
        return content_digest(self)
