from worldzero.data.observations import (
    ObservationClass,
    ObservationLineage,
    ObservationSeries,
    TransformRecord,
)

from tools.materialize_demography_temporal_split import render_macroregion_population_csv


def _series(
    *,
    observation_class: ObservationClass,
    geography: tuple[str, ...],
    values: tuple[float, ...],
    validation_eligible: bool,
    derived: bool = False,
) -> ObservationSeries:
    transform = (
        TransformRecord(
            transform_id="test-transform",
            version="1",
            code_commit="b" * 40,
            source_observable_ids=("source",),
        )
        if derived
        else None
    )
    return ObservationSeries(
        observable_id="derived" if derived else "source",
        observation_class=observation_class,
        unit="persons",
        geography=geography,
        time=tuple(2022 for _ in geography),
        values=values,
        lineage=(ObservationLineage(dataset_id="fixture", content_sha256="a" * 64),),
        validation_eligible=validation_eligible,
        transform=transform,
    )


def test_total_renderer_matches_governed_csv_contract() -> None:
    source = _series(
        observation_class=ObservationClass.OFFICIAL_ESTIMATE,
        geography=("parent-a", "parent-b"),
        values=(100.0, 200.0),
        validation_eligible=True,
    )
    aggregated = _series(
        observation_class=ObservationClass.DERIVED,
        geography=("region-a", "region-b"),
        values=(100.0, 200.0),
        validation_eligible=True,
        derived=True,
    )

    rendered = render_macroregion_population_csv(
        source=source,
        aggregated=aggregated,
        region_ids=("region-a", "region-b"),
        year=2022,
    )

    assert rendered == (
        b"region_id,year,population_persons,source_observation_class,"
        b"observation_class,validation_eligible\n"
        b"region-a,2022,100,OFFICIAL_ESTIMATE,DERIVED,true\n"
        b"region-b,2022,200,OFFICIAL_ESTIMATE,DERIVED,true\n"
    )


def test_total_renderer_rejects_non_estimate_source() -> None:
    source = _series(
        observation_class=ObservationClass.PROJECTION,
        geography=("parent-a",),
        values=(100.0,),
        validation_eligible=False,
    )
    aggregated = _series(
        observation_class=ObservationClass.DERIVED,
        geography=("region-a",),
        values=(100.0,),
        validation_eligible=False,
        derived=True,
    )

    try:
        render_macroregion_population_csv(
            source=source,
            aggregated=aggregated,
            region_ids=("region-a",),
            year=2022,
        )
    except ValueError as exc:
        assert "official estimate" in str(exc)
    else:
        raise AssertionError("non-estimate source must fail closed")
