from worldzero.data.observations import (
    ObservationClass,
    ObservationLineage,
    ObservationSeries,
)
from worldzero.data.transforms import per_capita


def _series(
    observable_id: str,
    dataset_id: str,
    digest: str,
    values: tuple[float, ...],
    unit: str,
) -> ObservationSeries:
    return ObservationSeries(
        observable_id=observable_id,
        observation_class=ObservationClass.DIRECT,
        unit=unit,
        geography=("north", "north"),
        time=(2020, 2021),
        values=values,
        lineage=(ObservationLineage(dataset_id=dataset_id, content_sha256=digest),),
    )


def test_per_capita_transform_preserves_both_raw_lineages_and_transform_identity():
    energy = _series("energy", "energy-raw", "a" * 64, (100.0, 120.0), "PJ")
    population = _series("population", "population-raw", "b" * 64, (10.0, 12.0), "persons")

    result = per_capita(
        energy,
        population,
        output_observable_id="energy_per_capita",
        output_unit="PJ/person",
        transform_version="1.0.0",
        transform_code_commit="c" * 40,
    )

    assert result.observation_class is ObservationClass.DERIVED
    assert result.values == (10.0, 10.0)
    assert {(item.dataset_id, item.content_sha256) for item in result.lineage} == {
        ("energy-raw", "a" * 64),
        ("population-raw", "b" * 64),
    }
    assert result.transform is not None
    assert result.transform.transform_id == "PER_CAPITA"
    assert result.transform.version == "1.0.0"


def test_per_capita_rejects_nonmatching_axes():
    energy = _series("energy", "energy-raw", "a" * 64, (100.0, 120.0), "PJ")
    population = ObservationSeries(
        observable_id="population",
        observation_class=ObservationClass.DIRECT,
        unit="persons",
        geography=("north", "south"),
        time=(2020, 2021),
        values=(10.0, 12.0),
        lineage=(ObservationLineage(dataset_id="population-raw", content_sha256="b" * 64),),
    )

    import pytest

    with pytest.raises(ValueError, match="axes"):
        per_capita(
            energy,
            population,
            output_observable_id="energy_per_capita",
            output_unit="PJ/person",
            transform_version="1.0.0",
            transform_code_commit="c" * 40,
        )


def test_projection_cannot_be_marked_validation_eligible():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="validation eligible"):
        ObservationSeries(
            observable_id="population_2026",
            observation_class=ObservationClass.PROJECTION,
            unit="persons",
            geography=("north",),
            time=(2026,),
            values=(1.0,),
            lineage=(ObservationLineage(dataset_id="wpp", content_sha256="a" * 64),),
            validation_eligible=True,
        )


def test_transform_inherits_bridge_only_status():
    projected_population = ObservationSeries(
        observable_id="population",
        observation_class=ObservationClass.PROJECTION,
        unit="persons",
        geography=("north", "north"),
        time=(2026, 2027),
        values=(10.0, 11.0),
        lineage=(ObservationLineage(dataset_id="population-projection", content_sha256="b" * 64),),
        validation_eligible=False,
    )
    energy = ObservationSeries(
        observable_id="energy",
        observation_class=ObservationClass.DIRECT,
        unit="PJ",
        geography=("north", "north"),
        time=(2026, 2027),
        values=(100.0, 110.0),
        lineage=(ObservationLineage(dataset_id="energy-raw", content_sha256="a" * 64),),
    )
    result = per_capita(
        energy,
        projected_population,
        output_observable_id="energy_per_capita",
        output_unit="PJ/person",
        transform_version="1.0.0",
        transform_code_commit="c" * 40,
    )
    assert not result.validation_eligible
