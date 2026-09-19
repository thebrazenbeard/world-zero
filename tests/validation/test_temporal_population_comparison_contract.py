import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from worldzero.validation.temporal_population import TemporalPopulationScoreReport
from worldzero.validation.temporal_population_comparison import (
    TemporalPopulationComparisonContract,
    load_temporal_population_comparison_contract,
    validate_benchmark_binding,
)

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_SUCCESSOR_VS_PERSISTENCE_COMPARISON_V1.yaml"
)
BENCHMARK = Path("state/results/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_V1.json")


def test_successor_comparison_contract_is_frozen_before_candidate_execution() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)

    assert contract.status == "FROZEN_PRE_CANDIDATE_EXECUTION"
    assert contract.max_fit_evidence_year == 2022
    assert contract.target_year == 2023
    assert contract.required_primary_improvements == (
        "MAE_PERSONS",
        "RMSE_PERSONS",
        "MAPE_PERCENT",
    )
    assert contract.require_global_absolute_error_not_worse is True
    assert contract.require_same_holdout_observations is True
    assert contract.allow_holdout_refit is False
    assert contract.first_candidate_evaluation_only is True
    assert contract.result_claim == "COMPARISON_ONLY"


def test_successor_comparison_contract_binds_frozen_persistence_result() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    benchmark = TemporalPopulationScoreReport.model_validate_json(
        BENCHMARK.read_bytes()
    )

    validate_benchmark_binding(contract=contract, benchmark=benchmark)


def test_successor_comparison_rejects_fit_evidence_reaching_holdout_year() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    payload = contract.model_dump(mode="python")
    payload["max_fit_evidence_year"] = 2023

    with pytest.raises(ValidationError, match="strictly after"):
        TemporalPopulationComparisonContract.model_validate(payload)


def test_successor_comparison_rejects_weakened_primary_metric_gate() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    payload = contract.model_dump(mode="python")
    payload["required_primary_improvements"] = ("MAE_PERSONS",)

    with pytest.raises(ValidationError, match="MAE/RMSE/MAPE"):
        TemporalPopulationComparisonContract.model_validate(payload)


def test_successor_comparison_rejects_benchmark_digest_substitution() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    benchmark = TemporalPopulationScoreReport.model_validate_json(
        BENCHMARK.read_bytes()
    )
    tampered = contract.model_copy(
        update={"benchmark_runtime_result_sha256": "0" * 64}
    )

    with pytest.raises(ValueError, match="runtime-result digest"):
        validate_benchmark_binding(contract=tampered, benchmark=benchmark)
