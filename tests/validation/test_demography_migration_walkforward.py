from pathlib import Path

from worldzero.sectors.demography import AgeCohort
from worldzero.validation.demography_walkforward import (
    compare_walkforward_scores,
    load_walkforward_contract,
    score_terminal_population,
)
from tools.run_demography_migration_walkforward import _balanced_migration_links

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_2017_TO_2018_V1.yaml"
)


def _cohorts(value: float) -> dict[AgeCohort, float]:
    return {cohort: value for cohort in AgeCohort}


def test_walkforward_contract_freezes_pre2018_firewall() -> None:
    contract = load_walkforward_contract(CONTRACT)

    assert contract.fit_years == (2016, 2017)
    assert contract.initialization_year == 2017
    assert contract.target_year == 2018
    assert contract.holdout_use["allowed_for_fit"] is False
    assert contract.holdout_use["allowed_for_model_selection"] is False
    assert contract.holdout_use["first_evaluation_only"] is True


def test_balanced_migration_links_conserve_flow() -> None:
    regions = ("a", "b")
    broad = {
        2016: {"a": _cohorts(100.0), "b": _cohorts(100.0)},
        2017: {"a": _cohorts(100.0), "b": _cohorts(100.0)},
    }
    vital = {
        2016: {
            "a": {"net_migration": -4.0},
            "b": {"net_migration": 4.0},
        },
        2017: {
            "a": {"net_migration": -4.0},
            "b": {"net_migration": 4.0},
        },
    }

    links, diagnostics = _balanced_migration_links(
        regions=regions,
        broad=broad,
        vital=vital,
        fit_years=(2016, 2017),
    )

    assert len(links) == 1
    assert links[0].source_region == "a"
    assert links[0].target_region == "b"
    assert links[0].annual_fraction == 0.01
    assert diagnostics["balanced_total_persons_per_year"] == 4.0


def test_walkforward_comparison_requires_older_adult_improvement() -> None:
    contract = load_walkforward_contract(CONTRACT)
    observed = {
        "a": {
            "child": 100.0,
            "young_adult": 100.0,
            "mature_adult": 100.0,
            "older_adult": 100.0,
        }
    }
    baseline = score_terminal_population(
        label="BASELINE_NO_MIGRATION",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal={
            "a": {
                "child": 90.0,
                "young_adult": 90.0,
                "mature_adult": 90.0,
                "older_adult": 90.0,
            }
        },
        observed=observed,
    )
    candidate = score_terminal_population(
        label="CANDIDATE_WITH_MIGRATION",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal={
            "a": {
                "child": 99.0,
                "young_adult": 99.0,
                "mature_adult": 99.0,
                "older_adult": 89.0,
            }
        },
        observed=observed,
    )

    report = compare_walkforward_scores(
        contract=contract,
        baseline=baseline,
        candidate=candidate,
    )

    assert report.mae_improved is True
    assert report.rmse_improved is True
    assert report.mape_improved is True
    assert report.older_adult_mape_improved is False
    assert report.result == "NOT_BETTER_WITH_MIGRATION"
