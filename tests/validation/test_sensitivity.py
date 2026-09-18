import pytest

from worldzero.calibration.parameters import ParameterBound
from worldzero.validation.sensitivity import morris_screen


def test_morris_screen_is_seeded_and_identifies_dominant_parameter():
    bounds = (
        ParameterBound("a", 0.0, 1.0),
        ParameterBound("b", 0.0, 1.0),
    )

    def model(params: dict[str, float]) -> float:
        return 10.0 * params["a"] + 0.1 * params["b"]

    first = morris_screen(model, bounds, trajectories=12, levels=6, seed=42)
    second = morris_screen(model, bounds, trajectories=12, levels=6, seed=42)

    assert first == second
    assert first.seed == 42
    assert first.effects["a"].mu_star > first.effects["b"].mu_star


def test_parameter_bounds_fail_on_invalid_range():
    with pytest.raises(ValueError, match="lower"):
        ParameterBound("x", 2.0, 1.0)
