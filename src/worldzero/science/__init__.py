"""Scientific comparison contracts for World Zero."""

from .benchmarks import BenchmarkManifest, PredictiveBenchmarkV1
from .canonical import canonical_json_bytes, content_digest
from .claims import ClaimRecord, ClaimRegistry, SourceRef
from .comparison_protocol import (
    ComparisonProtocol,
    ComparisonProtocolV1,
    ComparisonSubject,
    DecisionRule,
    MetricSpec,
)
from .implementation_coverage import (
    ImplementationBinding,
    ImplementationCoverage,
    ImplementationCoverageV1,
    validate_coverage,
)
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
    "BenchmarkManifest",
    "BenchmarkResultLabel",
    "CausalTopologyV2",
    "ClaimRecord",
    "ClaimRegistry",
    "ComparisonProtocol",
    "ComparisonProtocolV1",
    "ComparisonSubject",
    "ControlMode",
    "DecisionRule",
    "EvidenceClass",
    "IdentifiabilityClass",
    "ImplementationBinding",
    "ImplementationCoverage",
    "ImplementationCoverageV1",
    "KillTest",
    "LineageRef",
    "LineageRegistry",
    "MetricSpec",
    "PredictiveBenchmarkV1",
    "SourceRef",
    "StructuralResultLabel",
    "TopologyNode",
    "TopologyRelation",
    "canonical_json_bytes",
    "content_digest",
    "validate_coverage",
]
