from pathlib import Path

import pytest

from tools.run_demography_older_mortality_mass_normalization import (
    _normalize_regional_older_mortality,
)
from worldzero.sectors.demography import AgeCohort, DemographyRates
from worldzero.validation.older_mortality_mass_normalization import (
    compare_mass_normalization_scores,
    load_mass_normalization_contract,
    score_mass_normalization_terminal,
)

CONTRACT = Path(
    "science/scoring/"
    "WZ_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_2018_TO_2019_V1.yaml"
)


def _rates(older: float) -> DemographyRates:
    return DemographyRates(
        birth_rate_per_young_adult=0.02,
        mortality={
            AgeCohort.CHILD: 0.001,
            AgeCohort.YOUNG_ADULT: 0.002,
            AgeCohort.MATURE_ADULT: 0.01,
            AgeCohort.OLDER_ADULT: older,
        },
        ageing={
            AgeCohort.CHILD: 0.05,
            AgeCohort.YOUNG_ADULT: 0.04,
            AgeCohort.MATURE_ADULT: 0.04,
            AgeCohort.OLDER_ADULT: 0.0,
        },
    )


def test_mass_normalization_contract_freezes_2019_firewall() -> None:
    contract = load_mass_normalization_contract(CONTRACT)

    assert contract.history_years == (2016, 2017, 2018)
    assert contract.base_rate_fit_years == (2017, 2018)
    assert contract.initialization_year == 2018
    assert contract.target_year == 2019
    assert contract.candidate_method["target_use_for_normalization"] is False
    assert contract.holdout_use["allowed_for_fit"] is False
    assert contract.holdout_use["allowed_for_model_selection"] is False
    assert contract.holdout_use["first_evaluation_only"] is True


def test_normalization_preserves_regional_shape_and_reference_death_mass() -> None:
    global_rates = {"a": _rates(0.04), "b": _rates(0.04)}
    regional = {"a": 0.02, "b": 0.06}
    initial = {
        "a": {cohort: 100.0 for cohort in AgeCohort},
        "b": {cohort: 300.0 for cohort in AgeCohort},
    }

    normalized, receipt = _normalize_regional_older_mortality(
        global_shape_rates=global_rates,
        regional_older_mortality=regional,
        initial_population=initial,
    )

    assert normalized["a"] / normalized["b"] == pytest.approx(\n        regional["a"] / regional["b"]\n    )\n    assert receipt["reference_global_shape_death_mass_persons_per_year"] == 16.0
    assert receipt["unnormalized_regional_death_mass_persons_per_year"] == 20.0
    assert receipt["normalization_factor"] == 0.8
    assert receipt["normalized_regional_death_mass_persons_per_year"] == 16.0


def test_mass_normalization_requires_global_improvement_without_other_regression() -> None:
    contract = load_mass_normalization_contract(CONTRACT)
    observed = {
        "a": {
            "child": 100.0,
            "young_adult": 100.0,
            "mature_adult": 100.0,
            "older_adult": 100.0,
        }
    }
    baseline = score_mass_normalization_terminal(
        label="BASELINE_UNNORMALIZED_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal={
            "a": {
                "child": 99.0,
                "young_adult": 99.0,
                "mature_adult": 99.0,
                "older_adult": 98.0,
            }
        },
        observed=observed,
    )
    candidate = score_mass_normalization_terminal(
        label="CANDIDATE_MASS_NORMALIZED_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal={
            "a": {
                "child": 99.0,
                "young_adult": 99.0,
                "mature_adult": 99.0,
                "older_adult": 99.0,
            }
        },
        observed=observed,
    )

    report = compare_mass_normalization_scores(
        contract=contract,
        baseline=baseline,
        candidate=candidate,
    )

    assert report.global_absolute_error_improved is True
    assert report.older_adult_mae_not_worse is True
    assert report.older_adult_mape_not_worse is True
    assert report.mae_not_worse is True
    assert report.rmse_not_worse is True
    assert report.mape_not_worse is True
    assert report.result == "BETTER_MASS_NORMALIZED"
