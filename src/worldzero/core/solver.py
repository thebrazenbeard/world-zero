"""Deterministic solvers for World Zero stock-flow models."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from .clock import SimulationClock
from .interfaces import StockId
from .invariants import InvariantViolation
from .stocks import ModelState, StockFlowModel


class NumericalError(RuntimeError):
    """Raised when a model produces a non-finite numerical value."""


class DomainViolation(RuntimeError):
    """Raised when a stock leaves its declared domain."""


class Solver(Protocol):
    def step(
        self, model: StockFlowModel, state: ModelState, t: float, dt: float
    ) -> ModelState: ...


def _derivatives(model: StockFlowModel, state: ModelState, t: float) -> dict[StockId, float]:
    values = model.derivatives(state, t)
    for stock_id, derivative in values.items():
        if not math.isfinite(derivative):
            raise NumericalError(f"non-finite derivative for {stock_id}")
    return values


def _validated_state(model: StockFlowModel, values: dict[StockId, float]) -> ModelState:
    for stock_id, value in values.items():
        if not math.isfinite(value):
            raise NumericalError(f"non-finite state value for {stock_id}")
        spec = model.stock_by_id[stock_id]
        if spec.nonnegative and value < 0:
            raise DomainViolation(f"stock {stock_id} crossed below zero: {value}")
    return ModelState({str(stock_id): value for stock_id, value in values.items()})


def _advance(
    model: StockFlowModel,
    state: ModelState,
    derivative: dict[StockId, float],
    scale: float,
) -> ModelState:
    values = {
        stock_id: state.value(stock_id) + scale * derivative[stock_id]
        for stock_id in model.stock_by_id
    }
    return _validated_state(model, values)


class EulerSolver:
    def step(self, model: StockFlowModel, state: ModelState, t: float, dt: float) -> ModelState:
        return _advance(model, state, _derivatives(model, state, t), dt)


class RK4Solver:
    def step(self, model: StockFlowModel, state: ModelState, t: float, dt: float) -> ModelState:
        k1 = _derivatives(model, state, t)
        s2 = _advance(model, state, k1, dt / 2.0)
        k2 = _derivatives(model, s2, t + dt / 2.0)
        s3 = _advance(model, state, k2, dt / 2.0)
        k3 = _derivatives(model, s3, t + dt / 2.0)
        s4 = _advance(model, state, k3, dt)
        k4 = _derivatives(model, s4, t + dt)
        values = {
            stock_id: state.value(stock_id)
            + dt * (k1[stock_id] + 2 * k2[stock_id] + 2 * k3[stock_id] + k4[stock_id]) / 6.0
            for stock_id in model.stock_by_id
        }
        return _validated_state(model, values)


@dataclass(frozen=True, slots=True)
class Trajectory:
    times: tuple[float, ...]
    states: tuple[ModelState, ...]

    def series(self, stock_id: StockId | str) -> tuple[float, ...]:
        return tuple(state.value(stock_id) for state in self.states)


def _check_invariants(model: StockFlowModel, state: ModelState, t: float) -> None:
    for invariant in model.invariants:
        result = invariant(state, t)
        if not result.ok:
            detail = f": {result.message}" if result.message else ""
            raise InvariantViolation(f"{result.name}{detail}")


def solve(model: StockFlowModel, clock: SimulationClock, solver: Solver) -> Trajectory:
    times = clock.times()
    state = model.initial_state()
    states = [state]
    _check_invariants(model, state, times[0])
    for index in range(clock.step_count):
        state = solver.step(model, state, times[index], clock.dt)
        _check_invariants(model, state, times[index + 1])
        states.append(state)
    return Trajectory(times=times, states=tuple(states))
