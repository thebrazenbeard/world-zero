from pathlib import Path

from worldzero.models.bindings import (
    build_world_zero_v0_config,
    load_baseline_parameter_set,
)
from worldzero.sectors.demography import AgeCohort
from worldzero.validation.temporal_population import TemporalPopulationScoreReport
from worldzero.validation.temporal_population_comparison import (
    compare_temporal_population_scores,
    load_temporal_population_comparison_contract,
)

PARAMETERS = Path(
    "scenarios/parameters/WORLD_ZERO_2022_PRE2023_DYNAMICS_V1.yaml"
)
SCENARIO = Path("scenarios/2022_to_2023_pre2023_dynamics_v1.yaml")
BUNDLE = Path("data/bundles/WORLD_ZERO_2022_TEMPORAL_VALIDATION_DATA_V1.yaml")
COMPARISON = Path(
    "science/scoring/WZ_DEMOGRAPHY_SUCCESSOR_VS_PERSISTENCE_COMPARISON_V1.yaml"
)
BENCHMARK = Path("state/results/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_V1.json")


def _benchmark() -> TemporalPopulationScoreReport:
    return TemporalPopulationScoreReport.model_validate_json(BENCHMARK.read_bytes())


def _candidate(**updates) -> TemporalPopulationScoreReport:
    benchmark = _benchmark()
    defaults = {
        "score_contract_id": (
            "WZ_DEMOGRAPHY_2022_TO_2023_PRE2023_DYNAMICS_SCORE_CONTRACT_V1"
        ),
        "runtime_result_sha256": "1" * 64,
        "scenario_id": "WORLD_ZERO_2022_TO_2023_PRE2023_DYNAMICS_V1",
        "parameter_set_id": "WORLD_ZERO_2022_PRE2023_DYNAMICS_V1",
    }
    defaults.update(updates)
    return benchmark.model_copy(update=defaults)


def test_structural_ageing_candidate_is_bound_to_frozen_cohort_widths() -> None:
    parameters = load_baseline_parameter_set(PARAMETERS)
    rates = parameters.default_region.demography

    assert rates.birth_rate_per_young_adult == 0.0
    assert rates.mortality.child == 0.0
    assert rates.mortality.young_adult == 0.0
    assert rates.mortality.mature_adult == 0.0
    assert rates.mortality.older_adult == 0.0
    assert rates.ageing.child == 1.0 / 15.0
    assert rates.ageing.young_adult == 1.0 / 25.0
    assert rates.ageing.mature_adult == 1.0 / 25.0
    assert rates.ageing.older_adult == 0.0


def test_structural_ageing_candidate_builds_from_2022_initialization_only() -> None:
    config = build_world_zero_v0_config(
        root=Path("."),
        scenario_path=SCENARIO,
        data_bundle_path=BUNDLE,
        parameter_set_path=PARAMETERS,
    )

    assert config.native.start == 2022.0
    assert config.native.stop == 2023.0
    assert config.native.dt == 0.25
    assert all(
        rates.ageing[AgeCohort.CHILD] == 1.0 / 15.0
        and rates.ageing[AgeCohort.YOUNG_ADULT] == 1.0 / 25.0
        and rates.ageing[AgeCohort.MATURE_ADULT] == 1.0 / 25.0
        and rates.ageing[AgeCohort.OLDER_ADULT] == 0.0
        for rates in config.native.demography_rates.values()
    )


def test_comparison_requires_all_primary_metrics_and_global_error_gate() -> None:
    contract = load_temporal_population_comparison_contract(COMPARISON)
    benchmark = _benchmark()
    candidate = _candidate(
        mae_persons=benchmark.mae_persons - 1.0,
        rmse_persons=benchmark.rmse_persons - 1.0,
        mape_percent=benchmark.mape_percent - 0.000001,
        global_error_persons=benchmark.global_error_persons,
    )

    report = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=candidate,
    )

    assert report.disposition == "BETTER_THAN_PERSISTENCE"
    assert report.same_holdout_observations is True


def test_comparison_fails_if_any_primary_metric_does_not_improve() -> None:
    contract = load_temporal_population_comparison_contract(COMPARISON)
    benchmark = _benchmark()
    candidate = _candidate(
        mae_persons=benchmark.mae_persons - 1.0,
        rmse_persons=benchmark.rmse_persons,
        mape_percent=benchmark.mape_percent - 0.000001,
        global_error_persons=benchmark.global_error_persons,
    )

    report = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=candidate,
    )

    assert report.disposition == "NOT_BETTER_THAN_PERSISTENCE"


def test_comparison_fails_if_absolute_global_error_worsens() -> None:
    contract = load_temporal_population_comparison_contract(COMPARISON)
    benchmark = _benchmark()
    candidate = _candidate(
        mae_persons=benchmark.mae_persons - 1.0,
        rmse_persons=benchmark.rmse_persons - 1.0,
        mape_percent=benchmark.mape_percent - 0.000001,
        global_error_persons=-(abs(benchmark.global_error_persons) + 1.0),
    )

    report = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=candidate,
    )

    assert report.disposition == "NOT_BETTER_THAN_PERSISTENCE"


def test_comparison_rejects_changed_holdout_membership() -> None:
    contract = load_temporal_population_comparison_contract(COMPARISON)
    benchmark = _benchmark()
    candidate = _candidate(observations=benchmark.observations[:-1])

    try:
        compare_temporal_population_scores(
            contract=contract,
            benchmark=benchmark,
            candidate=candidate,
        )
    except ValueError as exc:
        assert "exact benchmark holdout observations" in str(exc)
    else:
        raise AssertionError("changed holdout membership must fail closed")
