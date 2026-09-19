from pathlib import Path

from tools.run_demography_older_mortality_walkforward import (
    _candidate_rates,
    _net_cohort_migration,
)
from worldzero.sectors.demography import AgeCohort, DemographyRates, MigrationLink
from worldzero.validation.older_mortality_walkforward import (
    compare_older_mortality_scores,
    load_older_mortality_contract,
    score_older_mortality_terminal,
)

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_OLDER_MORTALITY_WALKFORWARD_2014_TO_2015_V1.yaml"
)


def _rates(older_mortality: float) -> DemographyRates:
    return DemographyRates(
        birth_rate_per_young_adult=0.02,
        mortality={
            AgeCohort.CHILD: 0.001,
            AgeCohort.YOUNG_ADULT: 0.002,
            AgeCohort.MATURE_ADULT: 0.01,
            AgeCohort.OLDER_ADULT: older_mortality,
        },
        ageing={
            AgeCohort.CHILD: 0.05,
            AgeCohort.YOUNG_ADULT: 0.04,
            AgeCohort.MATURE_ADULT: 0.04,
            AgeCohort.OLDER_ADULT: 0.0,
        },
    )


def test_older_mortality_contract_freezes_2015_firewall() -> None:
    contract = load_older_mortality_contract(CONTRACT)

    assert contract.history_years == (2012, 2013, 2014)
    assert contract.base_rate_fit_years == (2013, 2014)
    assert contract.initialization_year == 2014
    assert contract.target_year == 2015
    assert contract.holdout_use["allowed_for_fit"] is False
    assert contract.holdout_use["allowed_for_model_selection"] is False
    assert contract.holdout_use["first_evaluation_only"] is True


def test_net_cohort_migration_is_conservative() -> None:
    stocks = {
        "a": {cohort: 100.0 for cohort in AgeCohort},
        "b": {cohort: 200.0 for cohort in AgeCohort},
    }
    links = (
        MigrationLink(source_region="a", target_region="b", annual_fraction=0.01),
    )

    a_net = _net_cohort_migration(
        region_id="a",
        cohort=AgeCohort.OLDER_ADULT,
        links=links,
        average_stock=stocks,
    )
    b_net = _net_cohort_migration(
        region_id="b",
        cohort=AgeCohort.OLDER_ADULT,
        links=links,
        average_stock=stocks,
    )

    assert a_net == -1.0
    assert b_net == 1.0
    assert a_net + b_net == 0.0


def test_candidate_rates_change_only_older_mortality() -> None:
    baseline = {"a": _rates(0.05)}
    candidate = _candidate_rates(
        baseline=baseline,
        regional_older_mortality={"a": 0.06},
    )

    assert candidate["a"].birth_rate_per_young_adult == baseline["a"].birth_rate_per_young_adult
    assert candidate["a"].ageing == baseline["a"].ageing
    assert candidate["a"].mortality[AgeCohort.CHILD] == baseline["a"].mortality[AgeCohort.CHILD]
    assert candidate["a"].mortality[AgeCohort.YOUNG_ADULT] == baseline["a"].mortality[AgeCohort.YOUNG_ADULT]
    assert candidate["a"].mortality[AgeCohort.MATURE_ADULT] == baseline["a"].mortality[AgeCohort.MATURE_ADULT]
    assert candidate["a"].mortality[AgeCohort.OLDER_ADULT] == 0.06


def test_comparison_requires_older_improvement_without_overall_regression() -> None:
    contract = load_older_mortality_contract(CONTRACT)
    observed = {
        "a": {
            "child": 100.0,
            "young_adult": 100.0,
            "mature_adult": 100.0,
            "older_adult": 100.0,
        }
    }
    baseline = score_older_mortality_terminal(
        label="BASELINE_GLOBAL_MORTALITY_SHAPE",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal={
            "a": {
                "child": 99.0,
                "young_adult": 99.0,
                "mature_adult": 99.0,
                "older_adult": 90.0,
            }
        },
        observed=observed,
    )
    candidate = score_older_mortality_terminal(
        label="CANDIDATE_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal={
            "a": {
                "child": 99.0,
                "young_adult": 99.0,
                "mature_adult": 99.0,
                "older_adult": 95.0,
            }
        },
        observed=observed,
    )

    report = compare_older_mortality_scores(
        contract=contract,
        baseline=baseline,
        candidate=candidate,
    )

    assert report.older_adult_mae_improved is True
    assert report.older_adult_mape_improved is True
    assert report.mae_not_worse is True
    assert report.rmse_not_worse is True
    assert report.mape_not_worse is True
    assert report.global_absolute_error_not_worse is True
    assert report.result == "BETTER_REGIONAL_OLDER_MORTALITY"
