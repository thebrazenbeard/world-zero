from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.canonical import content_digest
from worldzero.science.types import ControlMode, EvidenceClass

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
    model_config = ConfigDict(frozen=True)

    spatial: Literal["GLOBAL", "REGIONAL", "BILATERAL_NETWORK", "LOCAL_AGGREGATED"]
    regions: tuple[str, ...] = ()
    time_start: float | None = None
    time_end: float | None = None


class Uncertainty(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal[
        "PARAMETER",
        "MEASUREMENT",
        "STRUCTURAL",
        "SCENARIO",
        "DEEP_UNCERTAINTY",
        "NONE_DECLARED",
    ]
    distribution: str | None = None
    range: tuple[float, float] | None = None
    notes: str | None = None


class TopologyNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    kind: Literal[
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
    control_mode: ControlMode
    evidence_class: EvidenceClass
    scope: Scope
    uncertainty: Uncertainty | None = None
    units: str | None = None
    conservation_group: str | None = None
    observation_mapping: str | None = None
    notes: str | None = None


class TopologyRelation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    inputs: tuple[str, ...] = Field(min_length=1)
    outputs: tuple[str, ...] = Field(min_length=1)
    relation_type: Literal[
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
    functional_form_class: Literal[
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
    polarity: Literal[
        "POSITIVE", "NEGATIVE", "MIXED", "NON_MONOTONIC", "CONDITIONAL", "UNKNOWN"
    ]
    evidence_class: EvidenceClass
    control_mode: ControlMode
    scope: Scope
    uncertainty: Uncertainty
    lag_model: str | None = None
    equation_ref: str | None = None
    rival_relation_ids: tuple[str, ...] = ()
    kill_test_ids: tuple[str, ...] = ()
    notes: str | None = None


class KillTest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[A-Z0-9_]+$")
    claim_or_mechanism: str = Field(min_length=1)
    test: str = Field(min_length=1)
    failure_meaning: str = Field(min_length=1)
    minimum_evidence: str | None = None
    holdout_class: Literal[
        "TEMPORAL", "REGIONAL", "VARIABLE", "STRUCTURAL", "SHOCK", "NEGATIVE_CONTROL"
    ] | None = None


class CausalTopologyV2(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["CAUSAL_TOPOLOGY_V2"]
    topology_id: str = Field(min_length=1)
    model_family: ModelFamily
    status: Literal[
        "DRAFT",
        "FROZEN_CANDIDATE",
        "UNDER_TEST",
        "QUALIFIED_WITHIN_SCOPE",
        "REJECTED",
        "SUPERSEDED",
    ] = "DRAFT"
    description: str | None = None
    region_definition_id: str | None = None
    provenance_refs: tuple[str, ...] = ()
    nodes: tuple[TopologyNode, ...] = Field(min_length=1)
    relations: tuple[TopologyRelation, ...] = ()
    kill_tests: tuple[KillTest, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_integrity(self) -> "CausalTopologyV2":
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate node id")

        relation_ids = [relation.id for relation in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("duplicate relation id")

        kill_test_ids = [kill_test.id for kill_test in self.kill_tests]
        if len(kill_test_ids) != len(set(kill_test_ids)):
            raise ValueError("duplicate kill test id")

        known_nodes = set(node_ids)
        known_kill_tests = set(kill_test_ids)
        known_relations = set(relation_ids)
        for relation in self.relations:
            for node_id in (*relation.inputs, *relation.outputs):
                if node_id not in known_nodes:
                    raise ValueError(f"relation {relation.id} references missing node {node_id}")
            for kill_test_id in relation.kill_test_ids:
                if kill_test_id not in known_kill_tests:
                    raise ValueError(
                        f"relation {relation.id} references missing kill test {kill_test_id}"
                    )
            for rival_id in relation.rival_relation_ids:
                if ":" not in rival_id and rival_id not in known_relations:
                    raise ValueError(f"relation {relation.id} references missing rival {rival_id}")
        return self

    def digest(self) -> str:
        return content_digest(self.model_dump(mode="json", exclude_none=False))
