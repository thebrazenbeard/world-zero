"""Frozen historical walk-forward scoring for demography migration experiments."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DemographyMigrationWalkforwardContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_DEMOGRAPHY_MIGRATION_WALKFORWARD_V1"]
    experiment_id: str = Field(min_length=1)
    status: Literal["FROZEN_PRE_EXECUTION"]
    fit_years: tuple[int, int]
    initialization_year: int
    target_year: int
    source_age5_manifest: str = Field(min_length=1)
    source_demographic_manifest: str = Field(min_length=1)
    baseline_lineage_id: str = Field(min_length=1)
    candidate_lineage_id: str = Field(min_length=1)
    baseline_parameter_set_id: str = Field(min_length=1)
    candidate_parameter_set_id: str = Field(min_length=1)
    holdout_use: dict[str, bool]
    comparison: dict[str, object]
    result_claim: Literal["HISTORICAL_WALKFORWARD_COMPARISON_ONLY"]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> DemographyMigrationWalkforwardContract:
        if self.fit_years[1] != self.initialization_year:
            raise ValueError("second fit year must equal initialization year")
        if self.target_year != self.initialization_year + 1:
            raise ValueError("V1 walk-forward target must be exactly one year later")
        if self.fit_years[0] != self.initialization_year - 1:
            raise ValueError("V1 fitting window must be the two years ending at initialization")
        if self.holdout_use != {
            "allowed_for_fit": False,
            "allowed_for_model_selection": False,
            "first_evaluation_only": True,
        }:
            raise ValueError("holdout-use firewall does not match frozen V1 contract")
        required = self.comparison.get("require_strict_improvement")
        if required != [
            "MAE_PERSONS",
            "RMSE_PERSONS",
            "MAPE_PERCENT",
            "OLDER_ADULT_MAPE_PERCENT",
        ]:
            raise ValueError("comparison metric gate does not match frozen V1 contract")
        if self.comparison.get("require_global_absolute_error_not_worse") is not True:
            raise ValueError("global absolute-error gate must remain enabled")
        return self


class WalkforwardScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    label: Literal["BASELINE_NO_MIGRATION", "CANDIDATE_WITH_MIGRATION"]
    parameter_set_id: str
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation_count: int = Field(gt=0)
    mean_error_persons: float
    mae_persons: float
    rmse_persons: float
    mape_percent: float
    older_adult_mape_percent: float
    global_observed_persons: float
    global_predicted_persons: float
    global_error_persons: float
    per_cohort_mape_percent: dict[str, float]


class WalkforwardComparisonReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    schema_version: Literal["WORLD_ZERO_DEMOGRAPHY_MIGRATION_WALKFORWARD_REPORT_V1"]
    experiment_id: str
    result_claim: Literal["HISTORICAL_WALKFORWARD_COMPARISON_ONLY"]
    result: Literal["BETTER_WITH_MIGRATION", "NOT_BETTER_WITH_MIGRATION"]
    baseline: WalkforwardScore
    candidate: WalkforwardScore
    mae_improved: bool
    rmse_improved: bool
    mape_improved: bool
    older_adult_mape_improved: bool
    global_absolute_error_not_worse: bool


def load_walkforward_contract(path: Path) -> DemographyMigrationWalkforwardContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("walk-forward contract must be a mapping")
    return DemographyMigrationWalkforwardContract.model_validate(payload)


def score_terminal_population(
    *,
    label: Literal["BASELINE_NO_MIGRATION", "CANDIDATE_WITH_MIGRATION"],
    parameter_set_id: str,
    terminal: dict[str, dict[str, float]],
    observed: dict[str, dict[str, float]],
) -> WalkforwardScore:
    if set(terminal) != set(observed):
        raise ValueError("predicted and observed region sets differ")

    errors: list[float] = []
    squared: list[float] = []
    apes: list[float] = []
    per_cohort: dict[str, list[float]] = {}
    global_predicted = 0.0
    global_observed = 0.0
    canonical_rows: list[dict[str, object]] = []

    for region_id in sorted(observed):
        if set(terminal[region_id]) != set(observed[region_id]):
            raise ValueError("predicted and observed cohort sets differ")
        for cohort_id in sorted(observed[region_id]):
            predicted = float(terminal[region_id][cohort_id])
            actual = float(observed[region_id][cohort_id])
            if not math.isfinite(predicted) or predicted < 0:
                raise ValueError("predicted population must be finite and nonnegative")
            if not math.isfinite(actual) or actual <= 0:
                raise ValueError("observed population must be finite and positive")
            error = predicted - actual
            ape = abs(error) / actual * 100.0
            errors.append(error)
            squared.append(error * error)
            apes.append(ape)
            per_cohort.setdefault(cohort_id, []).append(ape)
            global_predicted += predicted
            global_observed += actual
            canonical_rows.append(
                {
                    "region_id": region_id,
                    "cohort_id": cohort_id,
                    "predicted_persons": predicted,
                    "observed_persons": actual,
                }
            )

    result_bytes = (
        json.dumps(canonical_rows, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")
    import hashlib

    result_sha256 = hashlib.sha256(result_bytes).hexdigest()
    per_cohort_mape = {
        cohort: sum(values) / len(values) for cohort, values in per_cohort.items()
    }
    return WalkforwardScore(
        label=label,
        parameter_set_id=parameter_set_id,
        result_sha256=result_sha256,
        observation_count=len(errors),
        mean_error_persons=sum(errors) / len(errors),
        mae_persons=sum(abs(value) for value in errors) / len(errors),
        rmse_persons=math.sqrt(sum(squared) / len(squared)),
        mape_percent=sum(apes) / len(apes),
        older_adult_mape_percent=per_cohort_mape["older_adult"],
        global_observed_persons=global_observed,
        global_predicted_persons=global_predicted,
        global_error_persons=global_predicted - global_observed,
        per_cohort_mape_percent=per_cohort_mape,
    )


def compare_walkforward_scores(
    *,
    contract: DemographyMigrationWalkforwardContract,
    baseline: WalkforwardScore,
    candidate: WalkforwardScore,
) -> WalkforwardComparisonReport:
    if baseline.parameter_set_id != contract.baseline_parameter_set_id:
        raise ValueError("baseline parameter-set identity mismatch")
    if candidate.parameter_set_id != contract.candidate_parameter_set_id:
        raise ValueError("candidate parameter-set identity mismatch")
    if baseline.observation_count != candidate.observation_count:
        raise ValueError("walk-forward observation counts differ")

    mae = candidate.mae_persons < baseline.mae_persons
    rmse = candidate.rmse_persons < baseline.rmse_persons
    mape = candidate.mape_percent < baseline.mape_percent
    older = candidate.older_adult_mape_percent < baseline.older_adult_mape_percent
    global_not_worse = abs(candidate.global_error_persons) <= abs(
        baseline.global_error_persons
    )
    better = mae and rmse and mape and older and global_not_worse
    return WalkforwardComparisonReport(
        schema_version="WORLD_ZERO_DEMOGRAPHY_MIGRATION_WALKFORWARD_REPORT_V1",
        experiment_id=contract.experiment_id,
        result_claim=contract.result_claim,
        result=(
            "BETTER_WITH_MIGRATION"
            if better
            else "NOT_BETTER_WITH_MIGRATION"
        ),
        baseline=baseline,
        candidate=candidate,
        mae_improved=mae,
        rmse_improved=rmse,
        mape_improved=mape,
        older_adult_mape_improved=older,
        global_absolute_error_not_worse=global_not_worse,
    )


def canonical_walkforward_report_bytes(report: WalkforwardComparisonReport) -> bytes:
    return (
        json.dumps(
            report.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
