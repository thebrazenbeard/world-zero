from pathlib import Path

import pytest
import yaml

from worldzero.reference.world3 import (
    World3OracleExecutionSpec,
    World3ReferenceProfile,
    World3ReferenceRegistry,
)


OBSERVABLES = (
    "POPULATION",
    "INDUSTRIAL_OUTPUT_PER_CAPITA",
    "FOOD_PER_CAPITA",
    "NONRENEWABLE_RESOURCE_FRACTION",
    "PERSISTENT_POLLUTION_INDEX",
)

BINDINGS = (
    {"observable_id": "POPULATION", "implementation_name": "pop"},
    {
        "observable_id": "INDUSTRIAL_OUTPUT_PER_CAPITA",
        "implementation_name": "iopc",
    },
    {"observable_id": "FOOD_PER_CAPITA", "implementation_name": "fpc"},
    {
        "observable_id": "NONRENEWABLE_RESOURCE_FRACTION",
        "implementation_name": "nrfr",
    },
    {
        "observable_id": "PERSISTENT_POLLUTION_INDEX",
        "implementation_name": "ppolx",
    },
)


def canonical_profile() -> World3ReferenceProfile:
    return World3ReferenceProfile(
        schema_version="WORLD3_REFERENCE_PROFILE_V1",
        profile_id="WORLD3_1974_STANDARD_RUN",
        variant="WORLD3_1974_DYNAMICS",
        role="CANONICAL_F0_CONTROL",
        scenario_id="STANDARD_RUN",
        observable_ids=OBSERVABLES,
        primary_references=(
            "Meadows et al. 1974, Dynamics of Growth in a Finite World",
        ),
    )


def pyworld3_oracle(**updates: object) -> World3OracleExecutionSpec:
    payload: dict[str, object] = {
        "schema_version": "WORLD3_ORACLE_EXECUTION_V1",
        "oracle_id": "PYWORLD3_1974_STANDARD",
        "profile_id": "WORLD3_1974_STANDARD_RUN",
        "implementation_ref": (
            "cvanwynsberghe/pyworld3@"
            "cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8"
        ),
        "start_year": 1900,
        "end_year": 2100,
        "timestep_years": 0.5,
        "endpoint_inclusive": True,
        "sample_count": 401,
        "delay_method": "EULER",
        "run_mode": "CHECKED_RESCHEDULE",
        "constants_mode": "IMPLEMENTATION_DEFAULTS",
        "tables_mode": "IMPLEMENTATION_DEFAULTS",
        "initialization_sequence": (
            "init_world3_constants",
            "init_world3_variables",
            "set_world3_table_functions",
            "set_world3_delay_functions",
            "run_world3",
        ),
        "observable_bindings": BINDINGS,
    }
    payload.update(updates)
    return World3OracleExecutionSpec.model_validate(payload)


def test_world3_generation_is_explicit():
    profile = canonical_profile()
    assert profile.variant == "WORLD3_1974_DYNAMICS"
    assert profile.role == "CANONICAL_F0_CONTROL"
    assert profile.scenario_id == "STANDARD_RUN"


def test_canonical_f0_rejects_world3_03():
    with pytest.raises(ValueError, match="canonical F0"):
        World3ReferenceProfile(
            **{
                **canonical_profile().model_dump(),
                "variant": "WORLD3_03_2004",
            }
        )


def test_reference_profile_requires_five_comparison_observables():
    with pytest.raises(ValueError, match="observables"):
        World3ReferenceProfile(
            **{
                **canonical_profile().model_dump(),
                "observable_ids": ("POPULATION",),
            }
        )


def test_registry_rejects_duplicate_profile_ids():
    profile = canonical_profile()
    with pytest.raises(ValueError, match="duplicate"):
        World3ReferenceRegistry((profile, profile))


def test_pyworld3_standard_run_uses_half_year_inclusive_grid():
    spec = pyworld3_oracle()
    assert spec.timestep_years == 0.5
    assert spec.endpoint_inclusive is True
    assert spec.sample_count == 401


def test_stale_one_year_assumption_is_rejected():
    with pytest.raises(ValueError, match="sample_count"):
        pyworld3_oracle(timestep_years=1.0)


def test_moving_upstream_oracle_ref_is_rejected():
    with pytest.raises(ValueError, match="exact GitHub commit"):
        pyworld3_oracle(implementation_ref="cvanwynsberghe/pyworld3@main")


def test_oracle_must_bind_all_five_comparison_series():
    with pytest.raises(ValueError, match="five F0 observables"):
        pyworld3_oracle(
            observable_bindings=(
                {"observable_id": "POPULATION", "implementation_name": "pop"},
            )
        )


def test_reference_and_oracle_seed_manifests_validate():
    profile_payload = yaml.safe_load(
        Path("reference_profiles/WORLD3_1974_STANDARD_RUN.yaml").read_text(
            encoding="utf-8"
        )
    )
    oracle_payload = yaml.safe_load(
        Path("oracle_specs/WORLD3_1974_PYWORLD3_STANDARD.yaml").read_text(
            encoding="utf-8"
        )
    )
    profile = World3ReferenceProfile.model_validate(profile_payload)
    oracle = World3OracleExecutionSpec.model_validate(oracle_payload)
    assert profile.profile_id == oracle.profile_id
    assert oracle.timestep_years == 0.5
    assert oracle.sample_count == 401
