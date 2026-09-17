"""Invariant results and failures for simulation runs."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InvariantResult:
    name: str
    ok: bool
    message: str = ""


class InvariantViolation(RuntimeError):
    """Raised when a declared model invariant fails."""
