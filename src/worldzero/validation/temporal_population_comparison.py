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
