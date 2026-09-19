import pytest

from worldzero.calibration.objective import CalibrationObjective, ObjectiveTerm
from worldzero.data.observations import ObservationClass, ObservationLineage, ObservationSeries
from worldzero.science.partitions import EvidencePartition, PartitionSet


def _partitions() -> PartitionSet:
    return PartitionSet(
        partition_set_id="p1",
        partitions=(
            EvidencePartition(
                partition_id="cal",
                partition_class="CALIBRATION",
                observation_ids=("o1", "o2"),
            ),
            EvidencePartition(
                partition_id="holdout",
                partition_class="TEMPORAL_HOLDOUT",
                observation_ids=("h1",),
            ),
        ),
    )


def test_calibration_objective_accepts_only_calibration_ids():
    objective = CalibrationObjective(
        partition_set=_partitions(),
        terms=(
            ObjectiveTerm("o1", observed=10.0, scale=2.0, weight=1.0),
            ObjectiveTerm("o2", observed=20.0, scale=5.0, weight=2.0),
        ),
    )
    result = objective.evaluate({"o1": 12.0, "o2": 15.0})
    assert result.term_ids == ("o1", "o2")
    assert result.weighted_squared_error == pytest.approx(3.0)


def test_holdout_observation_in_calibration_objective_fails_closed():
    with pytest.raises(ValueError, match="holdout"):
        CalibrationObjective(
            partition_set=_partitions(),
            terms=(ObjectiveTerm("h1", observed=3.0, scale=1.0, weight=1.0),),
        )


def test_missing_prediction_fails_instead_of_being_silently_dropped():
    objective = CalibrationObjective(
        partition_set=_partitions(),
        terms=(ObjectiveTerm("o1", observed=10.0, scale=2.0, weight=1.0),),
    )
    with pytest.raises(KeyError, match="o1"):
        objective.evaluate({})


def _observation(observable_id: str, *, validation_eligible: bool = True) -> ObservationSeries:
    return ObservationSeries(
        observable_id=observable_id,
        observation_class=ObservationClass.OFFICIAL_ESTIMATE,
        unit="persons",
        geography=("global",),
        time=(2023,),
        values=(1.0,),
        lineage=(ObservationLineage(dataset_id="fixture", content_sha256="a" * 64),),
        validation_eligible=validation_eligible,
    )


def test_holdout_selection_rejects_calibration_partition():
    from worldzero.validation.holdouts import select_holdout

    observations = {"h1": _observation("h1")}
    assert (
        select_holdout(_partitions(), "holdout", observations=observations).observation_ids
        == ("h1",)
    )
    with pytest.raises(ValueError, match="calibration"):
        select_holdout(_partitions(), "cal", observations={})


def test_holdout_selection_requires_governed_observation_binding():
    from worldzero.validation.holdouts import select_holdout

    with pytest.raises(ValueError, match="missing governed evidence binding"):
        select_holdout(_partitions(), "holdout", observations={})


def test_holdout_selection_rejects_mismatched_observation_identity():
    from worldzero.validation.holdouts import select_holdout

    with pytest.raises(ValueError, match="binding identity mismatch"):
        select_holdout(
            _partitions(),
            "holdout",
            observations={"h1": _observation("other")},
        )


def test_holdout_selection_rejects_validation_ineligible_observation():
    from worldzero.validation.holdouts import select_holdout

    with pytest.raises(ValueError, match="not validation eligible"):
        select_holdout(
            _partitions(),
            "holdout",
            observations={"h1": _observation("h1", validation_eligible=False)},
        )


def test_calibration_runner_requests_only_frozen_calibration_terms():
    from worldzero.calibration.parameters import ParameterBound, ParameterSpace
    from worldzero.calibration.runner import CalibrationRunner

    objective = CalibrationObjective(
        partition_set=_partitions(),
        terms=(ObjectiveTerm("o1", observed=5.0, scale=1.0, weight=1.0),),
    )
    runner = CalibrationRunner(
        parameter_space=ParameterSpace((ParameterBound("x", 0.0, 10.0),)),
        objective=objective,
    )
    requested: list[tuple[str, ...]] = []

    def predict(params, observation_ids):
        requested.append(observation_ids)
        return {"o1": params["x"]}

    result = runner.run(({"x": 0.0}, {"x": 5.0}, {"x": 7.0}), predict)
    assert result.best_parameters["x"] == pytest.approx(5.0)
    assert result.best_objective == pytest.approx(0.0)
    assert requested == [("o1",), ("o1",), ("o1",)]
