import math

import pytest

from worldzero.core.clock import SimulationClock
from worldzero.core.solver import DomainViolation, EulerSolver, NumericalError, solve
from worldzero.core.stocks import FlowSpec, ModelState, StockFlowModel, StockSpec


def _transfer_model() -> StockFlowModel:
    return StockFlowModel(
        stocks=(
            StockSpec("a", owner="core", unit="units", initial=100.0),
            StockSpec("b", owner="core", unit="units", initial=0.0),
        ),
        flows=(
            FlowSpec(
                "a_to_b",
                source="a",
                target="b",
                unit_per_time="units/year",
                rate=lambda state, _t: 0.1 * state.value("a"),
            ),
        ),
    )


def test_closed_stock_conserves_quantity():
    trajectory = solve(
        _transfer_model(),
        SimulationClock(start=0.0, stop=10.0, dt=0.25),
        EulerSolver(),
    )
    for state in trajectory.states:
        assert state.value("a") + state.value("b") == pytest.approx(100.0, abs=1e-9)


def test_nonfinite_flow_fails_closed():
    model = StockFlowModel(
        stocks=(StockSpec("x", owner="core", unit="units", initial=1.0),),
        flows=(
            FlowSpec(
                "bad",
                source=None,
                target="x",
                unit_per_time="units/year",
                rate=lambda _state, _t: math.nan,
            ),
        ),
    )
    with pytest.raises(NumericalError, match="non-finite"):
        solve(model, SimulationClock(0.0, 1.0, 0.25), EulerSolver())


def test_nonnegative_stock_cannot_cross_zero():
    model = StockFlowModel(
        stocks=(StockSpec("x", owner="core", unit="units", initial=1.0),),
        flows=(
            FlowSpec(
                "drain",
                source="x",
                target=None,
                unit_per_time="units/year",
                rate=lambda _state, _t: 2.0,
            ),
        ),
    )
    with pytest.raises(DomainViolation, match="x"):
        solve(model, SimulationClock(0.0, 1.0, 1.0), EulerSolver())


def test_model_state_rejects_unknown_stock():
    state = ModelState({"x": 1.0})
    with pytest.raises(KeyError):
        state.value("missing")
