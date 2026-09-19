from pathlib import Path

from worldzero.models.bindings import (
    build_world_zero_v0_config,
    load_baseline_data_bundle_manifest,
    load_baseline_parameter_set,
)
from worldzero.models.scenarios import load_scenario_manifest
from worldzero.validation.temporal_population import (
    load_temporal_population_scoring_contract,
)

SCENARIO = Path("scenarios/2022_to_2023_temporal_score_v1.yaml")
BUNDLE = Path("data/bundles/WORLD_ZERO_2022_TEMPORAL_VALIDATION_DATA_V1.yaml")
PARAMETERS = Path(
    "scenarios/parameters/WORLD_ZERO_2022_TEMPORAL_SCORE_PROVISIONAL_V1.yaml"
)
CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_CONTRACT_V1.yaml"
)


def test_temporal_score_controls_are_frozen_and_consistent() -> None:
    scenario = load_scenario_manifest(SCENARIO)
    bundle = load_baseline_data_bundle_manifest(BUNDLE)
    parameters = load_baseline_parameter_set(PARAMETERS)
    contract = load_temporal_population_scoring_contract(CONTRACT)

    assert scenario.status == "EXECUTABLE"
    assert scenario.start == 2022.0
    assert scenario.stop == 2023.0
    assert scenario.data_manifest_id == bundle.data_manifest_id
    assert scenario.parameter_set_id == parameters.parameter_set_id

    assert bundle.status == "READY"
    assert bundle.year == 2022
    assert contract.status == "FROZEN_PRE_EXECUTION"
    assert contract.scenario_id == scenario.scenario_id
    assert contract.data_manifest_id == bundle.data_manifest_id
    assert contract.parameter_set_id == parameters.parameter_set_id
    assert contract.initialization_year == 2022
    assert contract.target_year == 2023
    assert contract.acceptance_policy == "NONE_SCORE_ONLY"
    assert contract.result_claim == "SCORE_ONLY"
    assert contract.allow_refit_on_holdout is False


def test_temporal_score_runtime_config_is_bound_to_2022_initial_state() -> None:
    config = build_world_zero_v0_config(
        root=Path("."),
        scenario_path=SCENARIO,
        data_bundle_path=BUNDLE,
        parameter_set_path=PARAMETERS,
    )

    assert config.native.start == 2022.0
    assert config.native.stop == 2023.0
    assert config.native.dt == 0.25
    assert sum(
        value
        for cohorts in config.native.initial_population.values()
        for value in cohorts.values()
    ) > 0
