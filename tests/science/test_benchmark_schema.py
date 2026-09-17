import json
from pathlib import Path

from worldzero.science.benchmarks import BenchmarkManifest

SCHEMA = Path(__file__).parents[2] / "specs" / "BENCHMARK_V1.schema.json"


def test_static_benchmark_schema_matches_canonical_runtime_contract():
    static = json.loads(SCHEMA.read_text(encoding="utf-8"))
    runtime = BenchmarkManifest.model_json_schema()

    assert set(static["properties"]) == set(runtime["properties"])
    assert set(static["required"]) == set(runtime["required"])
    assert static["properties"]["causal_interpretation"]["const"] is False

    rules = static.get("allOf", [])
    b0 = [rule for rule in rules if _benchmark_id(rule) == "B0_PERSISTENCE_TREND"]
    b1 = [rule for rule in rules if _benchmark_id(rule) == "B1_REDUCED_FORM_EMPIRICAL"]
    assert b0 and b1
    assert {"feature_set", "hyperparameter_policy"} <= set(b1[0]["then"]["required"])


def _benchmark_id(rule: dict) -> str | None:
    return rule.get("if", {}).get("properties", {}).get("benchmark_id", {}).get("const")


def test_static_benchmark_schema_mirrors_runtime_method_guards():
    static = json.loads(SCHEMA.read_text(encoding="utf-8"))
    rules = static.get("allOf", [])
    b0 = next(rule for rule in rules if _benchmark_id(rule) == "B0_PERSISTENCE_TREND")
    b1 = next(rule for rule in rules if _benchmark_id(rule) == "B1_REDUCED_FORM_EMPIRICAL")
    regularized = next(
        rule
        for rule in rules
        if rule.get("if", {}).get("properties", {}).get("method", {}).get("const")
        == "REGULARIZED_VAR"
    )

    assert set(b0["then"]["properties"]["method"]["enum"]) == {
        "PERSISTENCE", "LINEAR_TREND", "LOG_LINEAR_TREND", "BOUNDED_LOGISTIC_TREND"
    }
    assert set(b1["then"]["properties"]["method"]["enum"]) == {
        "REGULARIZED_VAR", "DYNAMIC_FACTOR", "STATE_SPACE", "OTHER_PREREGISTERED_REDUCED_FORM"
    }
    assert "regularization_policy" in regularized["then"]["required"]
