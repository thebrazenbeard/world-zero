"""Executable stock-flow core for World Zero."""

from .clock import SimulationClock
from .interfaces import FlowId, Quantity, RegionId, SectorId, StockId
from .invariants import InvariantResult, InvariantViolation
from .solver import DomainViolation, EulerSolver, NumericalError, RK4Solver, Trajectory, solve
from .stocks import FlowSpec, ModelState, StockFlowModel, StockSpec

__all__ = [
    "DomainViolation",
    "EulerSolver",
    "FlowId",
    "FlowSpec",
    "InvariantResult",
    "InvariantViolation",
    "ModelState",
    "NumericalError",
    "Quantity",
    "RK4Solver",
    "RegionId",
    "SectorId",
    "SimulationClock",
    "StockFlowModel",
    "StockId",
    "StockSpec",
    "Trajectory",
    "solve",
]
