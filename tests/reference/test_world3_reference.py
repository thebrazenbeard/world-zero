import pytest

from worldzero.reference.world3 import World3ReferenceProfile, World3ReferenceRegistry


def canonical_profile():
    return World3ReferenceProfile(
        schema_version="WORLD3_REFERENCE_PROFILE_V1",
        profile_id="WORLD3_1974_STANDARD_RUN",
        variant="WORLD3_1974_DYNAMICS",
        role="CANONICAL_F0_CONTROL",
        start_year=1900,
        end_year=2100,
        timestep_years=1.0,
        integration_semantics="REFERENCE_BACKWARD_EULER_COMPATIBLE",
        observable_ids=(
            "POPULATION",
            "INDUSTRIAL_OUTPUT_PER_CAPITA",
            "FOOD_PER_CAPITA",
            "NONRENEWABLE_RESOURCE_FRACTION",
            "PERSISTENT_POLLUTION_INDEX",
        ),
        primary_references=(
            "Meadows et al. 1974, Dynamics of Growth in a Finite World",
        ),
        reference_implementations=(
            "cvanwynsberghe/pyworld3@cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8",
            "worlddynamics/WorldDynamics.jl@7315afe159dc23e2af5482c215669b2572545068",
        ),
    )


def test_world3_generation_is_explicit():
    profile = canonical_profile()
    assert profile.variant == "WORLD3_1974_DYNAMICS"
    assert profile.role == "CANONICAL_F0_CONTROL"


def test_canonical_f0_rejects_world3_03():
    with pytest.raises(ValueError, match="canonical F0"):
        World3ReferenceProfile(
            **{
                **canonical_profile().model_dump(),
                "variant": "WORLD3_03_2004",
            }
        )


def test_reference_profile_requires_exact_upstream_commit():
    with pytest.raises(ValueError, match="exact commit"):
        World3ReferenceProfile(
            **{
                **canonical_profile().model_dump(),
                "reference_implementations": ("cvanwynsberghe/pyworld3@main",),
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
