"""Bounded institutional response capacity and explicit policy delay."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstitutionParams:
    response_capacity: float
    implementation_delay: float

    def __post_init__(self) -> None:
        if not 0 <= self.response_capacity <= 1:
            raise ValueError("response_capacity must be within [0, 1]")
        if not math.isfinite(self.implementation_delay) or self.implementation_delay < 0:
            raise ValueError("implementation_delay must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class PolicyIntervention:
    start_time: float
    magnitude: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.magnitude):
            raise ValueError("policy intervention values must be finite")


@dataclass(frozen=True, slots=True)
class PolicyResponse:
    time: float
    requested_magnitude: float
    effective_magnitude: float
    active: bool


def policy_response(
    time: float,
    params: InstitutionParams,
    intervention: PolicyIntervention | None,
) -> PolicyResponse:
    if not math.isfinite(time):
        raise ValueError("policy response time must be finite")
    if intervention is None:
        return PolicyResponse(time, 0.0, 0.0, False)
    effective_time = intervention.start_time + params.implementation_delay
    active = time >= effective_time
    effective = intervention.magnitude * params.response_capacity if active else 0.0
    return PolicyResponse(
        time=time,
        requested_magnitude=intervention.magnitude,
        effective_magnitude=effective,
        active=active,
    )
