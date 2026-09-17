import json
from pathlib import Path

SCHEMA = Path(__file__).parents[2] / "specs" / "RUN_RECEIPT_V1.schema.json"


def test_static_receipt_schema_enforces_subject_class_identity_boundaries():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    subject = schema["$defs"]["ScientificSubjectIdentity"]
    rules = subject.get("allOf", [])

    causal = [
        rule for rule in rules
        if rule.get("if", {}).get("properties", {}).get("subject_class", {}).get("const")
        == "CAUSAL_FAMILY"
    ]
    benchmark = [
        rule for rule in rules
        if rule.get("if", {}).get("properties", {}).get("subject_class", {}).get("const")
        == "PREDICTIVE_BENCHMARK"
    ]
    assert causal and benchmark
    assert {"topology_digest", "implementation_coverage_digest"} <= set(
        causal[0]["then"]["required"]
    )
