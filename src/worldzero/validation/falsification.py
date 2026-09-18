"""Executable hostile falsification oracles for World Zero V0."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from worldzero.accounting.trade import TradeFlow, reconcile_trade
from worldzero.science.observations import ObservationMapping, summarize_independence


@dataclass(frozen=True, slots=True)
class OracleResult:
    oracle_id: str
    passed: bool
    details: Mapping[str, object]


def _result(oracle_id: str, passed: bool, **details: object) -> OracleResult:
    return OracleResult(
        oracle_id=oracle_id,
        passed=passed,
        details=MappingProxyType(dict(details)),
    )


def _relative_error(predicted: float, observed: float) -> float:
    return abs(predicted - observed) / max(abs(observed), 1e-12)


def aggregate_fit_oracle(
    *,
    observed_by_region: Mapping[str, float],
    predicted_by_region: Mapping[str, float],
    global_tolerance: float,
    regional_tolerance: float,
) -> OracleResult:
    if set(observed_by_region) != set(predicted_by_region):
        raise ValueError("observed and predicted region sets differ")
    observed_global = sum(observed_by_region.values())
    predicted_global = sum(predicted_by_region.values())
    global_error = _relative_error(predicted_global, observed_global)
    regional_errors = {
        region_id: _relative_error(predicted_by_region[region_id], observed)
        for region_id, observed in observed_by_region.items()
    }
    trap = global_error <= global_tolerance and any(
        error > regional_tolerance for error in regional_errors.values()
    )
    return _result(
        "F1_AGGREGATE_FIT_TRAP",
        not trap,
        global_relative_error=global_error,
        regional_relative_errors=regional_errors,
    )


def correlated_evidence_oracle(
    mappings: Iterable[ObservationMapping],
    *,
    claimed_independent_count: int,
) -> OracleResult:
    summary = summarize_independence(mappings)
    passed = claimed_independent_count <= summary.independent_group_count
    return _result(
        "F2_CORRELATED_EVIDENCE",
        passed,
        claimed_independent_count=claimed_independent_count,
        independent_group_count=summary.independent_group_count,
        group_ids=summary.group_ids,
    )


def identifiability_oracle(
    *,
    candidates: tuple[tuple[Mapping[str, float], float], ...],
    objective_tolerance: float,
    parameter_distance_threshold: float,
) -> OracleResult:
    if len(candidates) < 2:
        raise ValueError("identifiability oracle requires at least two candidates")
    if objective_tolerance < 0 or parameter_distance_threshold < 0:
        raise ValueError("identifiability tolerances must be nonnegative")
    parameter_ids = tuple(sorted(candidates[0][0]))
    if not parameter_ids:
        raise ValueError("candidate parameter sets must be non-empty")
    for params, objective in candidates:
        if tuple(sorted(params)) != parameter_ids:
            raise ValueError("candidate parameter sets use different parameter IDs")
        if not math.isfinite(objective) or not all(math.isfinite(v) for v in params.values()):
            raise ValueError("identifiability candidates must be finite")
    best = min(objective for _, objective in candidates)
    near_best = [item for item in candidates if item[1] <= best + objective_tolerance]
    max_distance = 0.0
    for index, (left, _) in enumerate(near_best):
        for right, _ in near_best[index + 1 :]:
            distance = math.sqrt(sum((left[name] - right[name]) ** 2 for name in parameter_ids))
            max_distance = max(max_distance, distance)
    return _result(
        "F3_IDENTIFIABILITY",
        max_distance <= parameter_distance_threshold,
        best_objective=best,
        near_best_count=len(near_best),
        max_parameter_distance=max_distance,
    )


def solver_convergence_oracle(
    *,
    reference: tuple[float, ...],
    alternatives: Mapping[str, tuple[float, ...]],
    relative_tolerance: float,
) -> OracleResult:
    if not reference:
        raise ValueError("solver reference must be non-empty")
    if relative_tolerance < 0:
        raise ValueError("relative_tolerance must be nonnegative")
    errors: dict[str, float] = {}
    for label, values in alternatives.items():
        if len(values) != len(reference):
            raise ValueError(f"solver result length differs for {label}")
        errors[label] = max(
            _relative_error(value, ref) for ref, value in zip(reference, values, strict=True)
        )
    return _result(
        "F5_SOLVER_TIMESTEP",
        all(error <= relative_tolerance for error in errors.values()),
        max_relative_errors=errors,
        tolerance=relative_tolerance,
    )


def technology_saturation_oracle(
    *,
    costs: tuple[float, ...],
    cost_floor: float,
    deployments: tuple[float, ...],
    deployment_limit: float,
) -> OracleResult:
    if not costs or len(costs) != len(deployments):
        raise ValueError("technology cost/deployment trajectories must be equal and non-empty")
    below_floor = min(costs) < cost_floor - 1e-12
    over_limit = max(deployments) > deployment_limit + 1e-12
    return _result(
        "F6_TECHNOLOGY_SATURATION",
        not below_floor and not over_limit,
        minimum_cost=min(costs),
        cost_floor=cost_floor,
        maximum_deployment=max(deployments),
        deployment_limit=deployment_limit,
    )


def trade_fragmentation_oracle(
    flows: Iterable[TradeFlow],
    *,
    tolerance: float = 1e-12,
) -> OracleResult:
    reconciliation = reconcile_trade(flows)
    difference = abs(reconciliation.difference)
    return _result(
        "F11_TRADE_FRAGMENTATION",
        difference <= tolerance,
        conservation_difference=reconciliation.difference,
        total_origin_debits=reconciliation.total_origin_debits,
        total_destination_credits=reconciliation.total_destination_credits,
        total_losses=reconciliation.total_losses,
    )
