"""Deterministic candidate calibration bound to a frozen objective and parameter space."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .objective import CalibrationObjective
from .parameters import ParameterSpace

PredictionFunction = Callable[[Mapping[str, float], tuple[str, ...]], Mapping[str, float]]


@dataclass(frozen=True, slots=True)
class CalibrationRunResult:
    partition_digest: str
    evaluated_candidate_count: int
    best_parameters: Mapping[str, float]
    best_objective: float


@dataclass(frozen=True, slots=True)
class CalibrationRunner:
    parameter_space: ParameterSpace
    objective: CalibrationObjective

    def run(
        self,
        candidates: Iterable[Mapping[str, float]],
        predict: PredictionFunction,
    ) -> CalibrationRunResult:
        term_ids = tuple(term.observation_id for term in self.objective.terms)
        best_parameters: dict[str, float] | None = None
        best_objective: float | None = None
        count = 0
        for raw_candidate in candidates:
            candidate = {key: float(value) for key, value in raw_candidate.items()}
            self.parameter_space.validate(candidate)
            predictions = dict(predict(candidate, term_ids))
            if set(predictions) != set(term_ids):
                raise ValueError(
                    "calibration predictor must return exactly the frozen objective observation IDs"
                )
            result = self.objective.evaluate(predictions)
            count += 1
            if best_objective is None or result.weighted_squared_error < best_objective:
                best_objective = result.weighted_squared_error
                best_parameters = candidate

        if best_parameters is None or best_objective is None:
            raise ValueError("calibration runner requires at least one candidate")
        return CalibrationRunResult(
            partition_digest=self.objective.partition_set.digest(),
            evaluated_candidate_count=count,
            best_parameters=MappingProxyType(best_parameters),
            best_objective=best_objective,
        )
