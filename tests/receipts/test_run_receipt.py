def _subject():
    from worldzero.receipts.run_receipt import ScientificSubjectIdentity

    return ScientificSubjectIdentity(
        subject_id="F1_MARKET_ADAPTIVE",
        subject_class="CAUSAL_FAMILY",
        source_commit="a" * 40,
        source_tree="b" * 40,
        topology_digest="c" * 64,
        manifest_digest="d" * 64,
        implementation_coverage_digest="e" * 64,
        dataset_manifest_set_digest="f" * 64,
        parameter_digest="1" * 64,
        region_set_digest="2" * 64,
        scenario_digest="3" * 64,
        observation_map_digest="4" * 64,
        calibration_partition_id="CAL",
        holdout_partition_ids=("H1",),
        comparison_protocol_digest="5" * 64,
    )


def _execution():
    from worldzero.receipts.run_receipt import ExecutionIdentity

    return ExecutionIdentity(
        solver_name="EULER",
        solver_version="1",
        timestep=0.25,
        tolerance=1e-6,
        random_seed=7,
        environment_fingerprint="env:cp312-linux",
    )


def test_solver_change_only_changes_execution_identity():
    from worldzero.receipts.run_receipt import RunReceipt

    base = RunReceipt(
        schema_version="RUN_RECEIPT_V1",
        receipt_id="RUN1",
        subject=_subject(),
        execution=_execution(),
    )
    a = base.with_solver("EULER")
    b = base.with_solver("RK45")
    assert a.subject.digest() == b.subject.digest()
    assert a.execution.digest() != b.execution.digest()
    assert a.digest() != b.digest()


def test_causal_subject_requires_topology_and_coverage():
    import pytest
    from pydantic import ValidationError

    from worldzero.receipts.run_receipt import ScientificSubjectIdentity

    data = _subject().model_dump()
    data["topology_digest"] = None
    data["implementation_coverage_digest"] = None
    with pytest.raises(ValidationError, match="causal"):
        ScientificSubjectIdentity.model_validate(data)


def test_benchmark_subject_cannot_claim_causal_topology():
    import pytest
    from pydantic import ValidationError

    from worldzero.receipts.run_receipt import ScientificSubjectIdentity

    data = _subject().model_dump()
    data.update(
        subject_id="B1_REDUCED_FORM_EMPIRICAL",
        subject_class="PREDICTIVE_BENCHMARK",
        implementation_coverage_digest=None,
    )
    with pytest.raises(ValidationError, match="benchmark"):
        ScientificSubjectIdentity.model_validate(data)
