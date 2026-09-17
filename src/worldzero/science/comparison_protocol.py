from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.science.canonical import content_digest

SubjectClass = Literal["CAUSAL_FAMILY", "PREDICTIVE_BENCHMARK"]
Aggregation = Literal["NONE", "MEAN", "MEDIAN", "WEIGHTED_MEAN", "MAX", "CUSTOM_FROZEN"]
MetricDirection = Literal["LOWER_IS_BETTER", "HIGHER_IS_BETTER", "WITHIN_RANGE"]
RuleType = Literal[
    "ABSOLUTE_TOLERANCE",
    "RELATIVE_TOLERANCE",
    "DIRECTIONAL_AGREEMENT",
    "BENCHMARK_MARGIN",
    "PARETO_NONDOMINANCE",
    "CUSTOM_FROZEN",
]
MissingSubjectPolicy = Literal["FAIL_COMPARISON", "DOWNGRADE_TO_EXPLORATORY"]
QualificationMode = Literal["CONFIRMATORY", "EXPLORATORY"]


class ComparisonSubject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str = Field(min_length=1)
    subject_class: SubjectClass
    expected_manifest_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MetricSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str = Field(min_length=1)
    observable_ids: tuple[str, ...] = Field(min_length=1)
    aggregation: Aggregation
    direction: MetricDirection
    target_range: tuple[float, float] | None = None

    @model_validator(mode="after")
    def validate_target_range(self) -> MetricSpec:
        if self.direction == "WITHIN_RANGE" and self.target_range is None:
            raise ValueError("WITHIN_RANGE metrics require target_range")
        if self.target_range is not None and self.target_range[0] > self.target_range[1]:
            raise ValueError("target_range lower bound exceeds upper bound")
        return self


class DecisionRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_type: RuleType
    metric_id: str | None = None
    threshold: float | None = None
    notes: str | None = None


class ComparisonProtocol(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["COMPARISON_PROTOCOL_V1"]
    protocol_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    purpose: str | None = None
    subjects: tuple[ComparisonSubject, ...] = Field(min_length=2)
    calibration_partition_id: str = Field(min_length=1)
    holdout_partition_ids: tuple[str, ...] = Field(min_length=1)
    metrics: tuple[MetricSpec, ...] = Field(min_length=1)
    decision_rules: tuple[DecisionRule, ...] = Field(min_length=1)
    missing_subject_policy: MissingSubjectPolicy
    identifiability_gate_id: str | None = None
    complexity_reporting_required: bool = True
    frozen_before_execution: bool
    exploratory: bool = False
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def force_posthoc_exploratory(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("frozen_before_execution") is False:
            data = dict(data)
            data["exploratory"] = True
        return data

    @model_validator(mode="after")
    def validate_protocol(self) -> ComparisonProtocol:
        subject_ids = [subject.subject_id for subject in self.subjects]
        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError("duplicate subject id")

        if len(self.holdout_partition_ids) != len(set(self.holdout_partition_ids)):
            raise ValueError("duplicate holdout partition id")
        if self.calibration_partition_id in self.holdout_partition_ids:
            raise ValueError("calibration partition cannot also be a holdout partition")

        metric_ids = [metric.metric_id for metric in self.metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("duplicate metric id")
        metric_id_set = set(metric_ids)

        rule_ids = [rule.rule_id for rule in self.decision_rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("duplicate decision rule id")
        unknown_metrics = sorted(
            {
                rule.metric_id
                for rule in self.decision_rules
                if rule.metric_id is not None and rule.metric_id not in metric_id_set
            }
        )
        if unknown_metrics:
            raise ValueError(
                "decision rules reference unknown metric ids: " + ", ".join(unknown_metrics)
            )
        return self

    @property
    def qualification_mode(self) -> QualificationMode:
        return "EXPLORATORY" if self.exploratory else "CONFIRMATORY"

    def freeze(self) -> ComparisonProtocol:
        return self

    def digest(self) -> str:
        return content_digest(self)
