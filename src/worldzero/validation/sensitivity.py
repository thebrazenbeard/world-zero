"""Deterministic Morris-style elementary-effects sensitivity screening."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.calibration.parameters import ParameterBound


@dataclass(frozen=True, slots=True)
class MorrisEffect:
    mu_star: float
    sigma: float
    sample_count: int


@dataclass(frozen=True, slots=True)
class MorrisScreenResult:
    seed: int
    levels: int
    trajectories: int
    effects: Mapping[str, MorrisEffect]


def _sample_standard_deviation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def morris_screen(
    model: Callable[[dict[str, float]], float],
    bounds: tuple[ParameterBound, ...],
    *,
    trajectories: int,
    levels: int,
    seed: int,
) -> MorrisScreenResult:
    if not bounds:
        raise ValueError("Morris screening requires at least one parameter bound")
    if len({bound.parameter_id for bound in bounds}) != len(bounds):
        raise ValueError("Morris parameter IDs must be unique")
    if trajectories < 1:
        raise ValueError("Morris trajectories must be positive")
    if levels < 3:
        raise ValueError("Morris levels must be at least 3")

    rng = random.Random(seed)
    delta = 1.0 / (levels - 1)
    effects: dict[str, list[float]] = {bound.parameter_id: [] for bound in bounds}
    for _ in range(trajectories):
        normalized = {
            bound.parameter_id: rng.randrange(0, levels - 1) / (levels - 1) for bound in bounds
        }
        base_params = {
            bound.parameter_id: bound.from_unit_interval(normalized[bound.parameter_id])
            for bound in bounds
        }
        base_value = float(model(base_params))
        if not math.isfinite(base_value):
            raise ValueError("sensitivity model returned a non-finite value")
        for bound in bounds:
            perturbed_normalized = dict(normalized)
            perturbed_normalized[bound.parameter_id] += delta
            perturbed_params = {
                candidate.parameter_id: candidate.from_unit_interval(
                    perturbed_normalized[candidate.parameter_id]
                )
                for candidate in bounds
            }
            perturbed_value = float(model(perturbed_params))
            if not math.isfinite(perturbed_value):
                raise ValueError("sensitivity model returned a non-finite value")
            effect = (perturbed_value - base_value) / delta
            effects[bound.parameter_id].append(effect)

    summaries = {
        parameter_id: MorrisEffect(
            mu_star=sum(abs(value) for value in values) / len(values),
            sigma=_sample_standard_deviation(values),
            sample_count=len(values),
        )
        for parameter_id, values in effects.items()
    }
    return MorrisScreenResult(
        seed=seed,
        levels=levels,
        trajectories=trajectories,
        effects=MappingProxyType(summaries),
    )
