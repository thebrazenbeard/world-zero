"""Scientific comparison contracts for World Zero."""

from .canonical import canonical_json_bytes, content_digest
from .claims import ClaimRecord, ClaimRegistry, SourceRef
from .lineage import LineageRef, LineageRegistry
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
    "ClaimRecord",
    "ClaimRegistry",
    "ControlMode",
    "EvidenceClass",
    "IdentifiabilityClass",
    "LineageRef",
    "LineageRegistry",
    "SourceRef",
    "StructuralResultLabel",
    "canonical_json_bytes",
    "content_digest",
]
