from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.canonical import content_digest

SubjectClass = Literal["CAUSAL_FAMILY", "PREDICTIVE_BENCHMARK"]


class ScientificSubjectIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str = Field(min_length=1)
    subject_class: SubjectClass
    source_commit: str = Field(pattern=r"^[0-9a-f]{40,64}$")
    source_tree: str = Field(pattern=r"^[0-9a-f]{40,64}$")
    topology_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    implementation_coverage_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    dataset_manifest_set_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    parameter_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    region_set_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    scenario_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation_map_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_partition_id: str = Field(min_length=1)
    holdout_partition_ids: tuple[str, ...] = Field(min_length=1)
    comparison_protocol_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_subject_class_bindings(self) -> ScientificSubjectIdentity:
        if self.subject_class == "CAUSAL_FAMILY":
            if self.topology_digest is None or self.implementation_coverage_digest is None:
                raise ValueError(
                    "causal subject requires topology and implementation coverage digests"
                )
        else:
            if self.topology_digest is not None or self.implementation_coverage_digest is not None:
                raise ValueError(
                    "benchmark subject cannot claim causal topology or implementation coverage"
                )
        if len(self.holdout_partition_ids) != len(set(self.holdout_partition_ids)):
            raise ValueError("duplicate holdout partition id")
        if self.calibration_partition_id in self.holdout_partition_ids:
            raise ValueError("calibration partition cannot also be a holdout partition")
        return self

    def digest(self) -> str:
        return content_digest(self)


class ExecutionIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    solver_name: str = Field(min_length=1)
    solver_version: str = Field(min_length=1)
    timestep: float = Field(gt=0)
    tolerance: float = Field(ge=0)
    random_seed: int = Field(ge=0)
    environment_fingerprint: str = Field(min_length=1)

    def digest(self) -> str:
        return content_digest(self)


class RunReceipt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["RUN_RECEIPT_V1"]
    receipt_id: str = Field(min_length=1)
    subject: ScientificSubjectIdentity
    execution: ExecutionIdentity
    result_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    def with_solver(self, solver_name: str) -> RunReceipt:
        execution = self.execution.model_copy(update={"solver_name": solver_name})
        return self.model_copy(update={"execution": execution})

    def digest(self) -> str:
        return content_digest(self)
