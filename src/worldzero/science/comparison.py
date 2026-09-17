from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from worldzero.science.comparison_protocol import ComparisonProtocol, MetricSpec
from worldzero.science.types import StructuralResultLabel

RunDirection = Literal["SUPPORTED", "NOT_SUPPORTED", "INDETERMINATE"]
SubjectClass = Literal["CAUSAL_FAMILY", "PREDICTIVE_BENCHMARK"]


class FamilyRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(min_length=1)
    subject_class: SubjectClass
    direction: RunDirection
    metrics: dict[str, float]
    valid: bool = True


class ClaimComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    structural_label: StructuralResultLabel
    causal_directions: dict[str, RunDirection]
    benchmark_labels: dict[str, str]
    missing_subject_ids: tuple[str, ...] = ()
    exploratory: bool = False


def _strictly_better(
    metric: MetricSpec,
    benchmark_value: float,
    causal_values: list[float],
) -> bool:
    if metric.direction == "LOWER_IS_BETTER":
        return benchmark_value < min(causal_values)
    if metric.direction == "HIGHER_IS_BETTER":
        return benchmark_value > max(causal_values)
    return False


def compare(
    protocol: ComparisonProtocol,
    results: dict[str, FamilyRunResult],
) -> ClaimComparison:
    declared = {subject.subject_id: subject for subject in protocol.subjects}
    missing = tuple(sorted(set(declared) - set(results)))
    if missing and protocol.missing_subject_policy == "FAIL_COMPARISON":
        raise ValueError("missing declared subjects: " + ", ".join(missing))

    extras = tuple(sorted(set(results) - set(declared)))
    if extras:
        raise ValueError("undeclared result subjects: " + ", ".join(extras))

    for subject_id, result in results.items():
        declared_subject = declared[subject_id]
        if result.subject_id != subject_id:
            raise ValueError(f"result key/subject mismatch: {subject_id}")
        if result.subject_class != declared_subject.subject_class:
            raise ValueError(f"subject class mismatch: {subject_id}")

    causal_results = [
        results[subject.subject_id]
        for subject in protocol.subjects
        if subject.subject_class == "CAUSAL_FAMILY" and subject.subject_id in results
    ]
    causal_directions = {
        result.subject_id: result.direction for result in causal_results
    }

    if missing or not causal_results:
        structural_label = StructuralResultLabel.UNKNOWN
    elif any(not result.valid or result.direction == "INDETERMINATE" for result in causal_results):
        structural_label = StructuralResultLabel.IDENTIFICATION_LIMITED
    elif len(causal_results) == 1:
        structural_label = StructuralResultLabel.CONTROL_ONLY
    elif len({result.direction for result in causal_results}) > 1:
        structural_label = StructuralResultLabel.FAMILY_SENSITIVE
    else:
        structural_label = StructuralResultLabel.ROBUST_ACROSS_FAMILIES

    benchmark_labels: dict[str, str] = {}
    valid_causal = [result for result in causal_results if result.valid]
    for subject in protocol.subjects:
        if subject.subject_class != "PREDICTIVE_BENCHMARK" or subject.subject_id not in results:
            continue
        benchmark = results[subject.subject_id]
        if not benchmark.valid or not valid_causal:
            continue

        comparable_metrics: list[MetricSpec] = []
        superior_flags: list[bool] = []
        for metric in protocol.metrics:
            if metric.metric_id not in benchmark.metrics:
                continue
            if any(metric.metric_id not in causal.metrics for causal in valid_causal):
                continue
            if metric.direction == "WITHIN_RANGE":
                continue
            comparable_metrics.append(metric)
            superior_flags.append(
                _strictly_better(
                    metric,
                    benchmark.metrics[metric.metric_id],
                    [causal.metrics[metric.metric_id] for causal in valid_causal],
                )
            )
        if comparable_metrics and all(superior_flags):
            benchmark_labels[subject.subject_id] = (
                "BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT"
            )

    return ClaimComparison(
        structural_label=structural_label,
        causal_directions=causal_directions,
        benchmark_labels=benchmark_labels,
        missing_subject_ids=missing,
        exploratory=protocol.exploratory or bool(missing),
    )
