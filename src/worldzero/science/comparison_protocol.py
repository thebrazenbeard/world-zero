"""Frozen comparison protocol contracts for qualification-grade runs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import content_digest


class ComparisonSubject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str = Field(min_length=1)
    subject_class: Literal["CAUSAL_FAMILY", "PREDICTIVE_BENCHMARK"]
    expected_manifest_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class ComparisonMetric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str = Field(min_length=1)
    observable_ids: tuple[str, ...] = Field(min_length=1)
    aggregation: Literal["NONE", "MEAN", "MEDIAN", "WEIGHTED_MEAN", "MAX", "CUSTOM_FROZEN"]
    direction: Literal["LOWER_IS_BETTER", "HIGHER_IS_BETTER", "WITHIN_RANGE"]
    target_range: tuple[float, float] | None = None

    @field_validator("observable_ids")
    @classmethod
    def unique_observables(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("metric observable_ids must be unique")
        return values

    @model_validator(mode="after")
    def validate_target_range(self) -> ComparisonMetric:
        if self.direction == "WITHIN_RANGE":
            if self.target_range is None or self.target_range[0] > self.target_range[1]:
                raise ValueError("WITHIN_RANGE requires ordered target_range")
        elif self.target_range is not None:
            raise ValueError("target_range is only valid for WITHIN_RANGE metrics")
        return self


class DecisionRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_type: Literal[
        "ABSOLUTE_TOLERANCE",
        "RELATIVE_TOLERANCE",
        "DIRECTIONAL_AGREEMENT",
        "BENCHMARK_MARGIN",
        "PARETO_NONDOMINANCE",
        "CUSTOM_FROZEN",
    ]
    metric_id: str | None = None
    threshold: float | None = None
    notes: str | None = None


class ComparisonProtocolV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["COMPARISON_PROTOCOL_V1"]
    protocol_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    purpose: str | None = None
    subjects: tuple[ComparisonSubject, ...] = Field(min_length=2)
    calibration_partition_id: str = Field(min_length=1)
    holdout_partition_ids: tuple[str, ...] = Field(min_length=1)
    metrics: tuple[ComparisonMetric, ...] = Field(min_length=1)
    decision_rules: tuple[DecisionRule, ...] = Field(min_length=1)
    missing_subject_policy: Literal["FAIL_COMPARISON", "DOWNGRADE_TO_EXPLORATORY"]
    identifiability_gate_id: str | None = None
    complexity_reporting_required: bool = True
    frozen_before_execution: bool
    exploratory: bool = False
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def force_posthoc_exploratory(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("frozen_before_execution") is False:
            normalized = dict(data)
            normalized["exploratory"] = True
            return normalized
        return data

    @property
    def qualification_mode(self) -> Literal["CONFIRMATORY", "EXPLORATORY"]:
        if self.exploratory or not self.frozen_before_execution:
            return "EXPLORATORY"
        return "CONFIRMATORY"

    @field_validator("holdout_partition_ids")
    @classmethod
    def unique_holdouts(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("holdout_partition_ids must be unique")
        return values

    @model_validator(mode="after")
    def validate_references(self) -> ComparisonProtocolV1:
        subject_ids = [subject.subject_id for subject in self.subjects]
        metric_ids = [metric.metric_id for metric in self.metrics]
        rule_ids = [rule.rule_id for rule in self.decision_rules]
        self._require_unique(subject_ids, "subject")
        self._require_unique(metric_ids, "metric")
        self._require_unique(rule_ids, "decision rule")

        metric_set = set(metric_ids)
        for rule in self.decision_rules:
            if rule.metric_id is not None and rule.metric_id not in metric_set:
                raise ValueError(f"decision rule {rule.rule_id} references missing metric {rule.metric_id}")
        return self

    @staticmethod
    def _require_unique(values: list[str], kind: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                raise ValueError(f"duplicate {kind} id: {value}")
            seen.add(value)

    def digest(self) -> str:
        return content_digest(self)

MetricSpec = ComparisonMetric
ComparisonProtocol = ComparisonProtocolV1
