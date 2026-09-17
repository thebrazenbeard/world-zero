import math

from worldzero.core.clock import SimulationClock
from worldzero.core.solver import EulerSolver, RK4Solver, solve
from worldzero.core.stocks import FlowSpec, StockFlowModel, StockSpec


def _growth_model() -> StockFlowModel:
    return StockFlowModel(
        stocks=(StockSpec("x", owner="core", unit="units", initial=1.0),),
        flows=(
            FlowSpec(
                "growth",
                source=None,
                target="x",
                unit_per_time="units/year",
                rate=lambda state, _t: state.value("x"),
            ),
        ),
    )


def _final_x(dt: float, solver) -> float:
    trajectory = solve(_growth_model(), SimulationClock(0.0, 1.0, dt), solver)
    return trajectory.states[-1].value("x")


def test_euler_converges_as_timestep_tightens():
    errors = [abs(_final_x(dt, EulerSolver()) - math.e) for dt in (0.5, 0.25, 0.125)]
    assert errors[2] < errors[1] < errors[0]


def test_rk4_is_more_accurate_than_euler_on_smooth_reference_ode():
    euler_error = abs(_final_x(0.25, EulerSolver()) - math.e)
    rk4_error = abs(_final_x(0.25, RK4Solver()) - math.e)
    assert rk4_error < euler_error
    assert rk4_error < 1e-4
