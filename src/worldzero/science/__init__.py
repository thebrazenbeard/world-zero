"""Scientific comparison contracts for World Zero."""

from .canonical import canonical_json_bytes, content_digest
from .claims import ClaimRecord, ClaimRegistry, SourceRef
from .lineage import LineageRef, LineageRegistry
from .topology import CausalTopologyV2, KillTest, TopologyNode, TopologyRelation
from .types import (
    AdmissionDisposition,
    BenchmarkResultLabel,
    ControlMode,
    EvidenceClass,
    IdentifiabilityClass,
    StructuralResultLabel,
)

__all__ = [
    "AdmissionDisposition",
    "BenchmarkResultLabel",
    "CausalTopologyV2",
    "ClaimRecord",
    "ClaimRegistry",
    "ControlMode",
    "EvidenceClass",
    "IdentifiabilityClass",
    "KillTest",
    "LineageRef",
    "LineageRegistry",
    "SourceRef",
    "StructuralResultLabel",
    "TopologyNode",
    "TopologyRelation",
    "canonical_json_bytes",
    "content_digest",
]
