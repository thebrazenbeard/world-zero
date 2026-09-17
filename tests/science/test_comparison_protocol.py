import json
from pathlib import Path

import pytest
from pydantic import ValidationError


def _subject(subject_id: str):
    from worldzero.science.comparison_protocol import ComparisonSubject

    return ComparisonSubject(subject_id=subject_id, subject_class="CAUSAL_FAMILY")


def _metric(threshold_variant: bool = False):
    from worldzero.science.comparison_protocol import MetricSpec

    return MetricSpec(
        metric_id="RMSE",
        observable_ids=("POPULATION",),
        aggregation="MEAN",
        direction="LOWER_IS_BETTER",
        target_range=None if not threshold_variant else (0.0, 1.0),
    )


def _rule(threshold: float = 0.1):
    from worldzero.science.comparison_protocol import DecisionRule

    return DecisionRule(
        rule_id="R1",
        rule_type="ABSOLUTE_TOLERANCE",
        metric_id="RMSE",
        threshold=threshold,
    )


def _protocol(*, subjects=None, frozen_before_execution: bool = True):
    from worldzero.science.comparison_protocol import ComparisonProtocol

    return ComparisonProtocol(
        schema_version="COMPARISON_PROTOCOL_V1",
        protocol_id="CP1",
        claim_id="C001",
        subjects=tuple(subjects or (_subject("F0"), _subject("F1"))),
        calibration_partition_id="CAL",
        holdout_partition_ids=("H1",),
        metrics=(_metric(),),
        decision_rules=(_rule(),),
        missing_subject_policy="FAIL_COMPARISON",
        frozen_before_execution=frozen_before_execution,
    )


def test_protocol_requires_at_least_two_subjects():
    with pytest.raises(ValidationError):
        _protocol(subjects=[_subject("F0")])


def test_frozen_protocol_rejects_metric_change():
    protocol = _protocol().freeze()
    with pytest.raises(ValidationError):
        protocol.metrics[0].threshold = 0.25


def test_protocol_frozen_after_result_inspection_is_exploratory():
    protocol = _protocol(frozen_before_execution=False)
    assert protocol.exploratory is True
    assert protocol.qualification_mode == "EXPLORATORY"


def test_protocol_digest_changes_when_decision_rule_changes():
    protocol = _protocol()
    changed = protocol.model_copy(update={"decision_rules": (_rule(0.2),)})
    assert protocol.digest() != changed.digest()


def test_duplicate_subject_ids_are_rejected():
    with pytest.raises(ValidationError, match="duplicate subject"):
        _protocol(subjects=[_subject("F0"), _subject("F0")])


def test_schema_represents_posthoc_analysis_only_as_exploratory():
    schema = json.loads(Path("specs/COMPARISON_PROTOCOL_V1.schema.json").read_text())
    assert schema["properties"]["frozen_before_execution"] == {"type": "boolean"}
    posthoc_rules = schema.get("allOf", [])
    assert any(
        rule.get("if", {}).get("properties", {}).get("frozen_before_execution")
        == {"const": False}
        and rule.get("then", {}).get("properties", {}).get("exploratory")
        == {"const": True}
        for rule in posthoc_rules
    )
