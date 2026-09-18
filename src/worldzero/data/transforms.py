"""Deterministic observation transforms that preserve source lineage."""

from __future__ import annotations

from worldzero.data.observations import (
    ObservationClass,
    ObservationLineage,
    ObservationSeries,
    TransformRecord,
)


def _merge_lineage(*series: ObservationSeries) -> tuple[ObservationLineage, ...]:
    by_key: dict[tuple[str, str], ObservationLineage] = {}
    for item in series:
        for lineage in item.lineage:
            key = (lineage.dataset_id, lineage.content_sha256)
            by_key[key] = lineage
    return tuple(by_key[key] for key in sorted(by_key))


def per_capita(
    numerator: ObservationSeries,
    denominator: ObservationSeries,
    *,
    output_observable_id: str,
    output_unit: str,
    transform_version: str,
    transform_code_commit: str,
) -> ObservationSeries:
    if numerator.geography != denominator.geography or numerator.time != denominator.time:
        raise ValueError("per-capita inputs must have identical axes")
    if any(value <= 0 for value in denominator.values):
        raise ValueError("per-capita denominator values must be positive")

    values = tuple(
        top / bottom for top, bottom in zip(numerator.values, denominator.values, strict=True)
    )
    transform = TransformRecord(
        transform_id="PER_CAPITA",
        version=transform_version,
        code_commit=transform_code_commit,
        source_observable_ids=(numerator.observable_id, denominator.observable_id),
    )
    return ObservationSeries(
        observable_id=output_observable_id,
        observation_class=ObservationClass.DERIVED,
        unit=output_unit,
        geography=numerator.geography,
        time=numerator.time,
        values=values,
        lineage=_merge_lineage(numerator, denominator),
        validation_eligible=(numerator.validation_eligible and denominator.validation_eligible),
        transform=transform,
    )
