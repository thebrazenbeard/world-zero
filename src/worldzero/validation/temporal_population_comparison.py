"""Frozen one-shot comparison contract for a pre-2023 demography successor."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.validation.temporal_population import TemporalPopulationScoreReport

_PRIMARY_METRICS = (
    "MAE_PERSONS",
    "RMSE_PERSONS",
    "MAPE_PERCENT",
)


class TemporalPopulationComparisonContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_TEMPORAL_POPULATION_COMPARISON_V1"]
    comparison_contract_id: str = Field(min_length=1)
    status: Literal["FROZEN_PRE_CANDIDATE_EXECUTION"]

    benchmark_score_path: str = Field(min_length=1)
    benchmark_score_contract_id: str = Field(min_length=1)
    benchmark_runtime_result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    candidate_lineage_id: str = Field(min_length=1)
    candidate_scenario_id: str = Field(min_length=1)
    candidate_parameter_set_id: str = Field(min_length=1)
    candidate_score_contract_id: str = Field(min_length=1)

    data_manifest_id: str = Field(min_length=1)
    holdout_partition_id: str = Field(min_length=1)
    target_year: int
    max_fit_evidence_year: int

    required_primary_improvements: tuple[str, ...]
    require_global_absolute_error_not_worse: Literal[True]
    require_same_holdout_observations: Literal[True]
    allow_holdout_refit: Literal[False]
    first_candidate_evaluation_only: Literal[True]
    result_claim: Literal["COMPARISON_ONLY"]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> TemporalPopulationComparisonContract:
        if self.target_year <= self.max_fit_evidence_year:
            raise ValueError(
                "target year must be strictly after every fitting-evidence year"
            )
        if self.required_primary_improvements != _PRIMARY_METRICS:
            raise ValueError(
                "successor comparison must require strict MAE/RMSE/MAPE improvement"
            )
        return self


def load_temporal_population_comparison_contract(
    path: Path,
) -> TemporalPopulationComparisonContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("temporal population comparison contract must be a mapping")
    return TemporalPopulationComparisonContract.model_validate(payload)


def validate_benchmark_binding(
    *,
    contract: TemporalPopulationComparisonContract,
    benchmark: TemporalPopulationScoreReport,
) -> None:
    if benchmark.score_contract_id != contract.benchmark_score_contract_id:
        raise ValueError("benchmark score-contract identity mismatch")
    if benchmark.runtime_result_sha256 != contract.benchmark_runtime_result_sha256:
        raise ValueError("benchmark runtime-result digest mismatch")
    if benchmark.data_manifest_id != contract.data_manifest_id:
        raise ValueError("benchmark data-bundle identity mismatch")
    if benchmark.holdout_partition_id != contract.holdout_partition_id:
        raise ValueError("benchmark holdout identity mismatch")
    if benchmark.target_year != contract.target_year:
        raise ValueError("benchmark target year mismatch")
    if benchmark.result_claim != "SCORE_ONLY":
        raise ValueError("benchmark must remain a score-only result")


class TemporalPopulationComparisonReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    schema_version: Literal["WORLD_ZERO_TEMPORAL_POPULATION_COMPARISON_REPORT_V1"]
    comparison_contract_id: str
    result_claim: Literal["COMPARISON_ONLY"]
    disposition: Literal["BETTER_THAN_PERSISTENCE", "NOT_BETTER_THAN_PERSISTENCE"]
    benchmark_runtime_result_sha256: str
    candidate_runtime_result_sha256: str
    benchmark_mae_persons: float
    candidate_mae_persons: float
    benchmark_rmse_persons: float
    candidate_rmse_persons: float
    benchmark_mape_percent: float
    candidate_mape_percent: float
    benchmark_absolute_global_error_persons: float
    candidate_absolute_global_error_persons: float
    same_holdout_observations: Literal[True]


def compare_temporal_population_scores(
    *,
    contract: TemporalPopulationComparisonContract,
    benchmark: TemporalPopulationScoreReport,
    candidate: TemporalPopulationScoreReport,
) -> TemporalPopulationComparisonReport:
    validate_benchmark_binding(contract=contract, benchmark=benchmark)

    if candidate.score_contract_id != contract.candidate_score_contract_id:
        raise ValueError("candidate score-contract identity mismatch")
    if candidate.scenario_id != contract.candidate_scenario_id:
        raise ValueError("candidate scenario identity mismatch")
    if candidate.parameter_set_id != contract.candidate_parameter_set_id:
        raise ValueError("candidate parameter-set identity mismatch")
    if candidate.data_manifest_id != contract.data_manifest_id:
        raise ValueError("candidate data-bundle identity mismatch")
    if candidate.holdout_partition_id != contract.holdout_partition_id:
        raise ValueError("candidate holdout identity mismatch")
    if candidate.target_year != contract.target_year:
        raise ValueError("candidate target year mismatch")
    if candidate.result_claim != "SCORE_ONLY":
        raise ValueError("candidate must remain a score-only result")

    benchmark_ids = tuple(item.observation_id for item in benchmark.observations)
    candidate_ids = tuple(item.observation_id for item in candidate.observations)
    if benchmark_ids != candidate_ids:
        raise ValueError("candidate must score the exact benchmark holdout observations")

    better = (
        candidate.mae_persons < benchmark.mae_persons
        and candidate.rmse_persons < benchmark.rmse_persons
        and candidate.mape_percent < benchmark.mape_percent
        and abs(candidate.global_error_persons) <= abs(benchmark.global_error_persons)
    )

    return TemporalPopulationComparisonReport(
        schema_version="WORLD_ZERO_TEMPORAL_POPULATION_COMPARISON_REPORT_V1",
        comparison_contract_id=contract.comparison_contract_id,
        result_claim=contract.result_claim,
        disposition=(
            "BETTER_THAN_PERSISTENCE"
            if better
            else "NOT_BETTER_THAN_PERSISTENCE"
        ),
        benchmark_runtime_result_sha256=benchmark.runtime_result_sha256,
        candidate_runtime_result_sha256=candidate.runtime_result_sha256,
        benchmark_mae_persons=benchmark.mae_persons,
        candidate_mae_persons=candidate.mae_persons,
        benchmark_rmse_persons=benchmark.rmse_persons,
        candidate_rmse_persons=candidate.rmse_persons,
        benchmark_mape_percent=benchmark.mape_percent,
        candidate_mape_percent=candidate.mape_percent,
        benchmark_absolute_global_error_persons=abs(
            benchmark.global_error_persons
        ),
        candidate_absolute_global_error_persons=abs(
            candidate.global_error_persons
        ),
        same_holdout_observations=True,
    )
