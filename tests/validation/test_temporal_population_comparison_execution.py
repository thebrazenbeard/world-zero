from pathlib import Path

import pytest

from worldzero.validation.temporal_population import TemporalPopulationScoreReport
from worldzero.validation.temporal_population_comparison import (
    compare_temporal_population_scores,
    load_temporal_population_comparison_contract,
)

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_SUCCESSOR_VS_PERSISTENCE_COMPARISON_V1.yaml"
)
BENCHMARK = Path("state/results/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_V1.json")


def _candidate(
    benchmark: TemporalPopulationScoreReport,
    *,
    mae: float,
    rmse: float,
    mape: float,
    global_error: float,
) -> TemporalPopulationScoreReport:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    return benchmark.model_copy(
        update={
            "score_contract_id": contract.candidate_score_contract_id,
            "runtime_result_sha256": "1" * 64,
            "scenario_id": contract.candidate_scenario_id,
            "parameter_set_id": contract.candidate_parameter_set_id,
            "mae_persons": mae,
            "rmse_persons": rmse,
            "mape_percent": mape,
            "global_error_persons": global_error,
        }
    )


def test_successor_comparison_emits_better_only_when_every_gate_passes() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    benchmark = TemporalPopulationScoreReport.model_validate_json(BENCHMARK.read_bytes())
    candidate = _candidate(
        benchmark,
        mae=benchmark.mae_persons - 1.0,
        rmse=benchmark.rmse_persons - 1.0,
        mape=benchmark.mape_percent - 0.001,
        global_error=0.0,
    )

    report = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=candidate,
    )

    assert report.result == "BETTER_THAN_PERSISTENCE"
    assert report.mae_improved is True
    assert report.rmse_improved is True
    assert report.mape_improved is True
    assert report.global_absolute_error_not_worse is True


def test_successor_comparison_fails_when_one_primary_metric_worsens() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    benchmark = TemporalPopulationScoreReport.model_validate_json(BENCHMARK.read_bytes())
    candidate = _candidate(
        benchmark,
        mae=benchmark.mae_persons - 1.0,
        rmse=benchmark.rmse_persons + 1.0,
        mape=benchmark.mape_percent - 0.001,
        global_error=0.0,
    )

    report = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=candidate,
    )

    assert report.result == "NOT_BETTER_THAN_PERSISTENCE"
    assert report.rmse_improved is False


def test_successor_comparison_rejects_changed_holdout_observation() -> None:
    contract = load_temporal_population_comparison_contract(CONTRACT)
    benchmark = TemporalPopulationScoreReport.model_validate_json(BENCHMARK.read_bytes())
    first = benchmark.observations[0].model_copy(
        update={"observed_persons": benchmark.observations[0].observed_persons + 1.0}
    )
    candidate = _candidate(
        benchmark,
        mae=benchmark.mae_persons - 1.0,
        rmse=benchmark.rmse_persons - 1.0,
        mape=benchmark.mape_percent - 0.001,
        global_error=0.0,
    ).model_copy(update={"observations": (first, *benchmark.observations[1:])})

    with pytest.raises(ValueError, match="holdout observations differ"):
        compare_temporal_population_scores(
            contract=contract,
            benchmark=benchmark,
            candidate=candidate,
        )
