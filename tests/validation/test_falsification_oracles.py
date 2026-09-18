from worldzero.accounting.trade import TradeFlow
from worldzero.science.observations import ObservationMapping
from worldzero.validation.falsification import (
    aggregate_fit_oracle,
    correlated_evidence_oracle,
    identifiability_oracle,
    solver_convergence_oracle,
    technology_saturation_oracle,
    trade_fragmentation_oracle,
)


def test_f1_aggregate_fit_trap_fails_regional_qualification():
    result = aggregate_fit_oracle(
        observed_by_region={"a": 100.0, "b": 100.0},
        predicted_by_region={"a": 150.0, "b": 50.0},
        global_tolerance=1e-9,
        regional_tolerance=0.1,
    )
    assert not result.passed
    assert result.oracle_id == "F1_AGGREGATE_FIT_TRAP"


def test_f2_correlated_indicators_are_not_counted_as_independent_confirmations():
    digest = "a" * 64
    mappings = (
        ObservationMapping(
            observable_id="gdp",
            dataset_id="d1",
            dataset_digest=digest,
            transform_digest=digest,
            upstream_lineage_id="shared-system",
            evidence_covariance_group_id="macro-cluster",
            evidence_class="OBSERVED",
            unit="index",
        ),
        ObservationMapping(
            observable_id="energy",
            dataset_id="d2",
            dataset_digest=digest,
            transform_digest=digest,
            upstream_lineage_id="shared-system",
            evidence_covariance_group_id="macro-cluster",
            evidence_class="OBSERVED",
            unit="index",
        ),
    )
    result = correlated_evidence_oracle(mappings, claimed_independent_count=2)
    assert not result.passed
    assert result.details["independent_group_count"] == 1


def test_f3_identifiability_detects_distant_parameter_sets_with_same_fit():
    result = identifiability_oracle(
        candidates=(
            ({"a": 1.0, "b": 1.0}, 1.00),
            ({"a": 9.0, "b": 9.0}, 1.01),
            ({"a": 1.1, "b": 1.1}, 1.20),
        ),
        objective_tolerance=0.02,
        parameter_distance_threshold=5.0,
    )
    assert not result.passed
    assert result.oracle_id == "F3_IDENTIFIABILITY"


def test_f5_solver_timestep_oracle_requires_declared_convergence():
    passed = solver_convergence_oracle(
        reference=(10.0, 20.0),
        alternatives={"euler_half_dt": (10.01, 19.99), "rk4": (10.0, 20.0)},
        relative_tolerance=0.01,
    )
    failed = solver_convergence_oracle(
        reference=(10.0, 20.0),
        alternatives={"coarse": (12.0, 20.0)},
        relative_tolerance=0.01,
    )
    assert passed.passed
    assert not failed.passed


def test_f6_technology_saturation_rejects_below_floor_or_overbuild():
    ok = technology_saturation_oracle(
        costs=(100.0, 80.0, 50.0),
        cost_floor=40.0,
        deployments=(10.0, 20.0, 30.0),
        deployment_limit=40.0,
    )
    below_floor = technology_saturation_oracle(
        costs=(100.0, 30.0),
        cost_floor=40.0,
        deployments=(10.0, 20.0),
        deployment_limit=40.0,
    )
    assert ok.passed
    assert not below_floor.passed


def test_f11_trade_fragmentation_must_still_conserve_physical_flow():
    before = (TradeFlow(origin="a", destination="b", amount=10.0, loss=1.0),)
    after = (
        TradeFlow(origin="a", destination="c", amount=6.0, loss=0.5),
        TradeFlow(origin="c", destination="b", amount=5.5, loss=0.5),
    )
    assert trade_fragmentation_oracle(before).passed
    assert trade_fragmentation_oracle(after).passed
