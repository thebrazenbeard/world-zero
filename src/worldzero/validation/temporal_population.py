"""Frozen scoring for governed temporal population holdouts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.models.execution import BaselineResultDocument, RuntimeReceipt
from worldzero.science.partitions import load_partition_set
from worldzero.science.population_evidence import (
    PopulationEvidenceObservation,
    load_population_evidence_catalog,
    verify_population_evidence_catalog,
    verify_temporal_population_evidence_partition,
)

_METRICS = (
    "MEAN_ERROR_PERSONS",
    "MAE_PERSONS",
    "RMSE_PERSONS",
    "MAPE_PERCENT",
    "GLOBAL_ERROR_PERSONS",
)


class TemporalPopulationScoringContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_TEMPORAL_POPULATION_SCORING_V1"]
    score_contract_id: str = Field(min_length=1)
    status: Literal["FROZEN_PRE_EXECUTION"]
    scenario_id: str = Field(min_length=1)
    data_manifest_id: str = Field(min_length=1)
    parameter_set_id: str = Field(min_length=1)
    evidence_catalog_path: str = Field(min_length=1)
    evidence_catalog_id: str = Field(min_length=1)
    partition_set_path: str = Field(min_length=1)
    partition_set_id: str = Field(min_length=1)
    initialization_partition_id: str = Field(min_length=1)
    holdout_partition_id: str = Field(min_length=1)
    initialization_year: int
    target_year: int
    prediction_stock_template: Literal["population:{region_id}:{cohort_id}"]
    metrics: tuple[str, ...]
    acceptance_policy: Literal["NONE_SCORE_ONLY"]
    result_claim: Literal["SCORE_ONLY"]
    allow_refit_on_holdout: Literal[False]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> "TemporalPopulationScoringContract":
        if self.target_year <= self.initialization_year:
            raise ValueError("target year must be strictly after initialization year")
        if self.metrics != _METRICS:
            raise ValueError("temporal score metric set/order does not match frozen V1 contract")
        return self


class TemporalPopulationObservationScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    observation_id: str
    region_id: str
    cohort_id: str
    observed_persons: float
    predicted_persons: float
    error_persons: float
    absolute_error_persons: float
    squared_error_persons2: float
    absolute_percentage_error_percent: float


class TemporalPopulationScoreReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    schema_version: Literal["WORLD_ZERO_TEMPORAL_POPULATION_SCORE_REPORT_V1"]
    score_contract_id: str
    result_claim: Literal["SCORE_ONLY"]
    acceptance_policy: Literal["NONE_SCORE_ONLY"]
    runtime_receipt_id: str
    runtime_source_commit: str
    runtime_result_sha256: str
    scenario_id: str
    data_manifest_id: str
    parameter_set_id: str
    initialization_year: int
    target_year: int
    holdout_partition_id: str
    observation_count: int
    mean_error_persons: float
    mae_persons: float
    rmse_persons: float
    mape_percent: float
    global_observed_persons: float
    global_predicted_persons: float
    global_error_persons: float
    observations: tuple[TemporalPopulationObservationScore, ...]


def load_temporal_population_scoring_contract(
    path: Path,
) -> TemporalPopulationScoringContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("temporal population scoring contract must be a mapping")
    return TemporalPopulationScoringContract.model_validate(payload)


def _resolve(root: Path, path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _observed_population(
    *,
    root: Path,
    observation: PopulationEvidenceObservation,
    cache: dict[str, list[dict[str, str]]],
) -> float:
    rows = cache.get(observation.manifest_path)
    if rows is None:
        manifest = load_derived_dataset_manifest(_resolve(root, observation.manifest_path))
        output_path = _resolve(root, manifest.output_path)
        rows = list(csv.DictReader(output_path.read_text(encoding="utf-8").splitlines()))
        cache[observation.manifest_path] = rows

    matches = [
        row
        for row in rows
        if row.get("region_id") == observation.region_id
        and row.get("year") == str(observation.year)
        and row.get("cohort_id") == observation.cohort_id
    ]
    if len(matches) != 1:
        raise ValueError("holdout observation must resolve to exactly one cohort row")
    value = float(matches[0]["population_persons"])
    if not math.isfinite(value) or value <= 0:
        raise ValueError("holdout population must be finite and positive")
    return value


def _verify_runtime_binding(
    *,
    result_path: Path,
    receipt_path: Path,
) -> tuple[BaselineResultDocument, RuntimeReceipt, str]:
    result_bytes = result_path.read_bytes()
    result_sha256 = hashlib.sha256(result_bytes).hexdigest()
    result = BaselineResultDocument.model_validate_json(result_bytes)
    receipt = RuntimeReceipt.model_validate_json(receipt_path.read_bytes())
    if receipt.result.sha256 != result_sha256:
        raise ValueError("runtime receipt result digest does not match scored result bytes")
    return result, receipt, result_sha256


def score_temporal_population_result(
    *,
    root: Path,
    contract_path: Path,
    result_path: Path,
    receipt_path: Path,
) -> TemporalPopulationScoreReport:
    contract = load_temporal_population_scoring_contract(contract_path)
    result, receipt, result_sha256 = _verify_runtime_binding(
        result_path=result_path,
        receipt_path=receipt_path,
    )

    if result.scenario_id != contract.scenario_id:
        raise ValueError("scored result scenario identity mismatch")
    if result.data_manifest_id != contract.data_manifest_id:
        raise ValueError("scored result data-bundle identity mismatch")
    if result.parameter_set_id != contract.parameter_set_id:
        raise ValueError("scored result parameter-set identity mismatch")
    if not result.times or result.times[-1] != float(contract.target_year):
        raise ValueError("scored result must terminate exactly at frozen target year")
    if len(result.times) != len(result.states):
        raise ValueError("scored result time/state cardinality mismatch")

    catalog = load_population_evidence_catalog(
        _resolve(root, contract.evidence_catalog_path)
    )
    if catalog.catalog_id != contract.evidence_catalog_id:
        raise ValueError("scoring evidence catalog identity mismatch")
    verify_population_evidence_catalog(root=root, catalog=catalog)

    partition_set = load_partition_set(_resolve(root, contract.partition_set_path))
    if partition_set.partition_set_id != contract.partition_set_id:
        raise ValueError("scoring partition-set identity mismatch")
    verify_temporal_population_evidence_partition(
        catalog=catalog,
        partition_set=partition_set,
    )

    initialization = next(
        (
            item
            for item in partition_set.partitions
            if item.partition_id == contract.initialization_partition_id
        ),
        None,
    )
    if initialization is None or initialization.partition_class != "INITIALIZATION":
        raise ValueError("frozen initialization partition binding mismatch")

    holdout = next(
        (
            item
            for item in partition_set.partitions
            if item.partition_id == contract.holdout_partition_id
        ),
        None,
    )
    if holdout is None or holdout.partition_class != "TEMPORAL_HOLDOUT":
        raise ValueError("frozen temporal holdout partition binding mismatch")

    by_id = {item.observation_id: item for item in catalog.observations}
    if {by_id[item].year for item in initialization.observation_ids} != {
        contract.initialization_year
    }:
        raise ValueError("initialization partition year mismatch")
    if {by_id[item].year for item in holdout.observation_ids} != {contract.target_year}:
        raise ValueError("holdout partition year mismatch")

    terminal_state = result.states[-1]
    observed_cache: dict[str, list[dict[str, str]]] = {}
    scores: list[TemporalPopulationObservationScore] = []

    for observation_id in holdout.observation_ids:
        observation = by_id[observation_id]
        if observation.role != "POPULATION_COHORT" or observation.cohort_id is None:
            raise ValueError("temporal population holdout must contain cohort observations")
        stock_id = contract.prediction_stock_template.format(
            region_id=observation.region_id,
            cohort_id=observation.cohort_id,
        )
        if stock_id not in terminal_state:
            raise ValueError("terminal model state is missing frozen holdout population stock")
        predicted = float(terminal_state[stock_id])
        if not math.isfinite(predicted) or predicted < 0:
            raise ValueError("predicted holdout population must be finite and nonnegative")
        observed = _observed_population(
            root=root,
            observation=observation,
            cache=observed_cache,
        )
        error = predicted - observed
        absolute_error = abs(error)
        scores.append(
            TemporalPopulationObservationScore(
                observation_id=observation_id,
                region_id=observation.region_id,
                cohort_id=observation.cohort_id,
                observed_persons=observed,
                predicted_persons=predicted,
                error_persons=error,
                absolute_error_persons=absolute_error,
                squared_error_persons2=error * error,
                absolute_percentage_error_percent=(absolute_error / observed) * 100.0,
            )
        )

    if not scores:
        raise ValueError("temporal holdout contains no scoreable observations")

    count = len(scores)
    mean_error = sum(item.error_persons for item in scores) / count
    mae = sum(item.absolute_error_persons for item in scores) / count
    rmse = math.sqrt(sum(item.squared_error_persons2 for item in scores) / count)
    mape = (
        sum(item.absolute_percentage_error_percent for item in scores) / count
    )
    global_observed = sum(item.observed_persons for item in scores)
    global_predicted = sum(item.predicted_persons for item in scores)

    return TemporalPopulationScoreReport(
        schema_version="WORLD_ZERO_TEMPORAL_POPULATION_SCORE_REPORT_V1",
        score_contract_id=contract.score_contract_id,
        result_claim=contract.result_claim,
        acceptance_policy=contract.acceptance_policy,
        runtime_receipt_id=receipt.receipt_id,
        runtime_source_commit=receipt.source_commit,
        runtime_result_sha256=result_sha256,
        scenario_id=result.scenario_id,
        data_manifest_id=result.data_manifest_id,
        parameter_set_id=result.parameter_set_id,
        initialization_year=contract.initialization_year,
        target_year=contract.target_year,
        holdout_partition_id=holdout.partition_id,
        observation_count=count,
        mean_error_persons=mean_error,
        mae_persons=mae,
        rmse_persons=rmse,
        mape_percent=mape,
        global_observed_persons=global_observed,
        global_predicted_persons=global_predicted,
        global_error_persons=global_predicted - global_observed,
        observations=tuple(scores),
    )


def canonical_score_report_bytes(report: TemporalPopulationScoreReport) -> bytes:
    return (
        json.dumps(
            report.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
