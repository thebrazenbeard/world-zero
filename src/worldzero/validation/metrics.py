"""Per-observable validation metrics without a universal model score."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeriesMetrics:
    observable_id: str
    region_id: str | None
    rmse: float
    mae: float
    bias: float
    turning_point_error: int
    interval_coverage: float | None
    sample_count: int


def _validate_series(name: str, values: tuple[float, ...], expected_length: int) -> None:
    if len(values) != expected_length:
        raise ValueError(f"{name} length does not match observed series")
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} contains non-finite values")


def evaluate_series(
    *,
    observable_id: str,
    region_id: str | None,
    observed: tuple[float, ...],
    predicted: tuple[float, ...],
    lower: tuple[float, ...] | None = None,
    upper: tuple[float, ...] | None = None,
) -> SeriesMetrics:
    if not observable_id.strip():
        raise ValueError("observable_id must be non-empty")
    if not observed:
        raise ValueError("validation series must be non-empty")
    _validate_series("observed", observed, len(observed))
    _validate_series("predicted", predicted, len(observed))
    errors = tuple(
        prediction - actual for actual, prediction in zip(observed, predicted, strict=True)
    )
    rmse = math.sqrt(sum(error**2 for error in errors) / len(errors))
    mae = sum(abs(error) for error in errors) / len(errors)
    bias = sum(errors) / len(errors)
    observed_peak = max(range(len(observed)), key=observed.__getitem__)
    predicted_peak = max(range(len(predicted)), key=predicted.__getitem__)

    coverage: float | None = None
    if (lower is None) != (upper is None):
        raise ValueError("lower and upper uncertainty bounds must be supplied together")
    if lower is not None and upper is not None:
        _validate_series("lower", lower, len(observed))
        _validate_series("upper", upper, len(observed))
        covered = 0
        for actual, lo, hi in zip(observed, lower, upper, strict=True):
            if lo > hi:
                raise ValueError("uncertainty lower bound exceeds upper bound")
            covered += int(lo <= actual <= hi)
        coverage = covered / len(observed)

    return SeriesMetrics(
        observable_id=observable_id,
        region_id=region_id,
        rmse=rmse,
        mae=mae,
        bias=bias,
        turning_point_error=abs(predicted_peak - observed_peak),
        interval_coverage=coverage,
        sample_count=len(observed),
    )
