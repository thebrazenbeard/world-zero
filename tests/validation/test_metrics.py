import pytest

from worldzero.validation.metrics import evaluate_series


def test_validation_returns_multi_metric_bundle_without_overall_score():
    result = evaluate_series(
        observable_id="population",
        region_id="north",
        observed=(10.0, 12.0, 14.0, 13.0),
        predicted=(10.0, 11.0, 15.0, 13.0),
    )
    assert result.observable_id == "population"
    assert result.region_id == "north"
    assert result.rmse == pytest.approx((0.5) ** 0.5)
    assert result.mae == pytest.approx(0.5)
    assert result.bias == pytest.approx(0.0)
    assert result.turning_point_error == 0
    assert not hasattr(result, "overall_score")


def test_interval_coverage_is_reported_separately():
    result = evaluate_series(
        observable_id="x",
        region_id=None,
        observed=(1.0, 2.0, 3.0),
        predicted=(1.0, 2.0, 3.0),
        lower=(0.5, 2.1, 2.5),
        upper=(1.5, 2.5, 3.5),
    )
    assert result.interval_coverage == pytest.approx(2 / 3)
