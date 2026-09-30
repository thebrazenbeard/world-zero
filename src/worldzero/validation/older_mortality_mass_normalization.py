"""Frozen older-mortality mass-normalization historical walk-forward."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OlderMortalityMassNormalizationContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[
        "WORLD_ZERO_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_V1"
    ]
    experiment_id: str = Field(min_length=1)
    status: Literal["FROZEN_PRE_EXECUTION"]
    history_years: tuple[int, int, int]
    base_rate_fit_years: tuple[int, int]
    older_mortality_transitions: tuple[tuple[int, int], tuple[int, int]]
    initialization_year: int
    target_year: int
    source_age5_manifest: str = Field(min_length=1)
    source_demographic_manifest: str = Field(min_length=1)
    baseline_lineage_id: str = Field(min_length=1)
    candidate_lineage_id: str = Field(min_length=1)
    baseline_parameter_set_id: str = Field(min_length=1)
    candidate_parameter_set_id: str = Field(min_length=1)
    candidate_method: dict[str, object]
    holdout_use: dict[str, bool]
    comparison: dict[str, object]
    result_claim: Literal["HISTORICAL_WALKFORWARD_COMPARISON_ONLY"]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> OlderMortalityMassNormalizationContract:
        if self.history_years != (2016, 2017, 2018):
            raise ValueError("V1 history years must remain frozen at 2016-2018")
        if self.base_rate_fit_years != (2017, 2018):
            raise ValueError("V1 base-rate fitting window must remain 2017-2018")
        if self.older_mortality_transitions != ((2016, 2017), (2017, 2018)):
            raise ValueError("V1 older-mortality transitions do not match frozen history")
        if self.initialization_year != 2018 or self.target_year != 2019:
            raise ValueError("V1 initialization/target years must remain 2018->2019")
        if self.candidate_method.get("target_use_for_normalization") is not False:
            raise ValueError("normalization must not use target evidence")
        if self.holdout_use != {
            "allowed_for_fit": False,
            "allowed_for_model_selection": False,
            "first_evaluation_only": True,
        }:
            raise ValueError("holdout-use firewall does not match frozen V1 contract")
        if self.comparison.get("require_strict_improvement") != [
            "GLOBAL_ABSOLUTE_ERROR_PERSONS"
        ]:
            raise ValueError("strict global-error gate does not match frozen V1 contract")
        if self.comparison.get("require_not_worse") != [
            "OLDER_ADULT_MAE_PERSONS",
            "OLDER_ADULT_MAPE_PERCENT",
            "MAE_PERSONS",
            "RMSE_PERSONS",
            "MAPE_PERCENT",
        ]:
            raise ValueError("not-worse gate does not match frozen V1 contract")
        return self


class MassNormalizationScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    label: Literal[
        "BASELINE_UNNORMALIZED_REGIONAL_OLDER_MORTALITY",
        "CANDIDATE_MASS_NORMALIZED_REGIONAL_OLDER_MORTALITY",
    ]
    parameter_set_id: str
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation_count: int = Field(gt=0)
    mean_error_persons: float
    mae_persons: float
    rmse_persons: float
    mape_percent: float
    older_adult_mae_persons: float
    older_adult_mape_percent: float
    global_observed_persons: float
    global_predicted_persons: float
    global_error_persons: float
    per_cohort_mae_persons: dict[str, float]
    per_cohort_mape_percent: dict[str, float]


class MassNormalizationComparisonReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    schema_version: Literal[
        "WORLD_ZERO_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_REPORT_V1"
    ]
    experiment_id: str
    result_claim: Literal["HISTORICAL_WALKFORWARD_COMPARISON_ONLY"]
    result: Literal["BETTER_MASS_NORMALIZED", "NOT_BETTER_MASS_NORMALIZED"]
    baseline: MassNormalizationScore
    candidate: MassNormalizationScore
    global_absolute_error_improved: bool
    older_adult_mae_not_worse: bool
    older_adult_mape_not_worse: bool
    mae_not_worse: bool
    rmse_not_worse: bool
    mape_not_worse: bool


def load_mass_normalization_contract(
    path: Path,
) -> OlderMortalityMassNormalizationContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("mass-normalization contract must be a mapping")
    return OlderMortalityMassNormalizationContract.model_validate(payload)


def score_mass_normalization_terminal(
    *,
    label: Literal[
        "BASELINE_UNNORMALIZED_REGIONAL_OLDER_MORTALITY",
        "CANDIDATE_MASS_NORMALIZED_REGIONAL_OLDER_MORTALITY",
    ],
    parameter_set_id: str,
    terminal: dict[str, dict[str, float]],
    observed: dict[str, dict[str, float]],
) -> MassNormalizationScore:
    if set(terminal) != set(observed):
        raise ValueError("predicted and observed region sets differ")

    errors: list[float] = []
    squared: list[float] = []
    apes: list[float] = []
    cohort_abs: dict[str, list[float]] = {}
    cohort_apes: dict[str, list[float]] = {}
    rows: list[dict[str, object]] = []
    global_predicted = 0.0
    global_observed = 0.0

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
            absolute = abs(error)
            ape = absolute / actual * 100.0
            errors.append(error)
            squared.append(error * error)
            apes.append(ape)
            cohort_abs.setdefault(cohort_id, []).append(absolute)
            cohort_apes.setdefault(cohort_id, []).append(ape)
            global_predicted += predicted
            global_observed += actual
            rows.append(
                {
                    "region_id": region_id,
                    "cohort_id": cohort_id,
                    "predicted_persons": predicted,
                    "observed_persons": actual,
                }
            )

    row_bytes = (
        json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")
    cohort_mae = {
        cohort: sum(values) / len(values) for cohort, values in cohort_abs.items()
    }
    cohort_mape = {
        cohort: sum(values) / len(values) for cohort, values in cohort_apes.items()
    }
    return MassNormalizationScore(
        label=label,
        parameter_set_id=parameter_set_id,
        result_sha256=hashlib.sha256(row_bytes).hexdigest(),
        observation_count=len(errors),
        mean_error_persons=sum(errors) / len(errors),
        mae_persons=sum(abs(value) for value in errors) / len(errors),
        rmse_persons=math.sqrt(sum(squared) / len(squared)),
        mape_percent=sum(apes) / len(apes),
        older_adult_mae_persons=cohort_mae["older_adult"],
        older_adult_mape_percent=cohort_mape["older_adult"],
        global_observed_persons=global_observed,
        global_predicted_persons=global_predicted,
        global_error_persons=global_predicted - global_observed,
        per_cohort_mae_persons=cohort_mae,
        per_cohort_mape_percent=cohort_mape,
    )


def compare_mass_normalization_scores(
    *,
    contract: OlderMortalityMassNormalizationContract,
    baseline: MassNormalizationScore,
    candidate: MassNormalizationScore,
) -> MassNormalizationComparisonReport:
    if baseline.parameter_set_id != contract.baseline_parameter_set_id:
        raise ValueError("baseline parameter-set identity mismatch")
    if candidate.parameter_set_id != contract.candidate_parameter_set_id:
        raise ValueError("candidate parameter-set identity mismatch")
    if baseline.observation_count != candidate.observation_count:
        raise ValueError("walk-forward observation counts differ")

    global_improved = abs(candidate.global_error_persons) < abs(
        baseline.global_error_persons
    )
    older_mae = candidate.older_adult_mae_persons <= baseline.older_adult_mae_persons
    older_mape = (
        candidate.older_adult_mape_percent <= baseline.older_adult_mape_percent
    )
    mae = candidate.mae_persons <= baseline.mae_persons
    rmse = candidate.rmse_persons <= baseline.rmse_persons
    mape = candidate.mape_percent <= baseline.mape_percent
    better = global_improved and older_mae and older_mape and mae and rmse and mape

    return MassNormalizationComparisonReport(
        schema_version=(
            "WORLD_ZERO_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_REPORT_V1"
        ),
        experiment_id=contract.experiment_id,
        result_claim=contract.result_claim,
        result="BETTER_MASS_NORMALIZED" if better else "NOT_BETTER_MASS_NORMALIZED",
        baseline=baseline,
        candidate=candidate,
        global_absolute_error_improved=global_improved,
        older_adult_mae_not_worse=older_mae,
        older_adult_mape_not_worse=older_mape,
        mae_not_worse=mae,
        rmse_not_worse=rmse,
        mape_not_worse=mape,
    )


def canonical_mass_normalization_report_bytes(
    report: MassNormalizationComparisonReport,
) -> bytes:
    return (
        json.dumps(
            report.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
