import pytest

from worldzero.science.comparison_protocol import ComparisonProtocolV1


def protocol_payload() -> dict:
    return {
        "schema_version": "COMPARISON_PROTOCOL_V1",
        "protocol_id": "CMP_POPULATION_V1",
        "claim_id": "C001",
        "subjects": [
            {"subject_id": "F0_WORLD3", "subject_class": "CAUSAL_FAMILY"},
            {"subject_id": "B0_POPULATION", "subject_class": "PREDICTIVE_BENCHMARK"},
        ],
        "calibration_partition_id": "CAL_1900_1990",
        "holdout_partition_ids": ["HOLDOUT_1991_2020"],
        "metrics": [
            {
                "metric_id": "NRMSE",
                "observable_ids": ["POPULATION"],
                "aggregation": "MEAN",
                "direction": "LOWER_IS_BETTER",
            }
        ],
        "decision_rules": [
            {"rule_id": "R1", "rule_type": "BENCHMARK_MARGIN", "metric_id": "NRMSE", "threshold": 0.05}
        ],
        "missing_subject_policy": "FAIL_COMPARISON",
        "frozen_before_execution": True,
    }


def test_protocol_requires_frozen_subject_set():
    protocol = ComparisonProtocolV1.model_validate(protocol_payload())
    assert protocol.frozen_before_execution is True
    assert len(protocol.subjects) == 2


def test_protocol_rejects_unknown_metric_reference():
    payload = protocol_payload()
    payload["decision_rules"][0]["metric_id"] = "MISSING"
    with pytest.raises(ValueError, match="MISSING"):
        ComparisonProtocolV1.model_validate(payload)


def test_within_range_requires_ordered_target_range():
    payload = protocol_payload()
    payload["metrics"][0].update({"direction": "WITHIN_RANGE", "target_range": [2.0, 1.0]})
    with pytest.raises(ValueError, match="target_range"):
        ComparisonProtocolV1.model_validate(payload)


def test_protocol_rejects_duplicate_subject_ids():
    payload = protocol_payload()
    payload["subjects"][1]["subject_id"] = "F0_WORLD3"
    with pytest.raises(ValueError, match="duplicate subject"):
        ComparisonProtocolV1.model_validate(payload)


def test_posthoc_protocol_is_forced_exploratory():
    payload = protocol_payload()
    payload["frozen_before_execution"] = False
    protocol = ComparisonProtocolV1.model_validate(payload)
    assert protocol.exploratory is True
    assert protocol.qualification_mode == "EXPLORATORY"


def test_static_comparison_schema_represents_posthoc_exploration():
    import json
    from pathlib import Path

    schema_path = Path(__file__).parents[2] / "specs" / "COMPARISON_PROTOCOL_V1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["properties"]["frozen_before_execution"] == {"type": "boolean"}
    assert any(
        rule.get("if", {}).get("properties", {}).get("frozen_before_execution", {}).get("const")
        is False
        for rule in schema.get("allOf", [])
    )


def test_static_schema_requires_explicit_exploratory_for_posthoc_protocol():
    import json
    from pathlib import Path

    schema_path = Path(__file__).parents[2] / "specs" / "COMPARISON_PROTOCOL_V1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    posthoc_rules = [
        rule
        for rule in schema.get("allOf", [])
        if rule.get("if", {}).get("properties", {}).get("frozen_before_execution", {}).get("const")
        is False
    ]
    assert posthoc_rules
    assert "exploratory" in posthoc_rules[0].get("then", {}).get("required", [])
