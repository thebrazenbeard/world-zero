import pytest

from worldzero.science.implementation_coverage import ImplementationCoverageV1


def coverage_payload() -> dict:
    return {
        "schema_version": "IMPLEMENTATION_COVERAGE_V1",
        "coverage_id": "COV_F0_V1",
        "topology_id": "F0_WORLD3_TOPOLOGY",
        "topology_digest": "a" * 64,
        "source_commit": "b" * 40,
        "bindings": [
            {
                "topology_object_id": "REL_POP_BIRTHS",
                "object_kind": "RELATION",
                "module": "worldzero.f0.population",
                "symbol": "birth_flow",
                "binding_status": "BOUND",
                "micro_test_ids": ["TEST_REL_POP_BIRTHS_POLARITY"],
            }
        ],
        "undeclared_runtime_relations": [],
        "missing_declared_relations": [],
        "coverage_status": "PASS",
    }


def test_pass_requires_relation_micro_tests():
    payload = coverage_payload()
    payload["bindings"][0]["micro_test_ids"] = []
    with pytest.raises(ValueError, match="micro"):
        ImplementationCoverageV1.model_validate(payload)


def test_pass_rejects_unbound_binding():
    payload = coverage_payload()
    payload["bindings"][0]["binding_status"] = "UNBOUND"
    with pytest.raises(ValueError, match="UNBOUND"):
        ImplementationCoverageV1.model_validate(payload)


def test_pass_rejects_missing_declared_relation():
    payload = coverage_payload()
    payload["missing_declared_relations"] = ["REL_MISSING"]
    with pytest.raises(ValueError, match="missing_declared_relations"):
        ImplementationCoverageV1.model_validate(payload)


def test_duplicate_binding_is_rejected():
    payload = coverage_payload()
    payload["bindings"].append(dict(payload["bindings"][0]))
    with pytest.raises(ValueError, match="duplicate binding"):
        ImplementationCoverageV1.model_validate(payload)


def test_exact_topology_reconciliation_rejects_missing_active_relation():
    import json
    from pathlib import Path

    from worldzero.science.implementation_coverage import validate_coverage
    from worldzero.science.topology import CausalTopologyV2

    fixture = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"
    topology = CausalTopologyV2.model_validate(json.loads(fixture.read_text(encoding="utf-8")))
    payload = coverage_payload()
    payload["topology_id"] = topology.topology_id
    payload["topology_digest"] = topology.digest()
    payload["bindings"] = []
    coverage = ImplementationCoverageV1.model_validate(payload)
    with pytest.raises(ValueError, match="DEMAND_RESPONSE"):
        validate_coverage(topology, coverage)


def test_exact_reconciliation_rejects_declared_binding_mismatch():
    import json
    from pathlib import Path

    from worldzero.science.implementation_coverage import validate_coverage
    from worldzero.science.topology import CausalTopologyV2

    fixture = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    raw["relations"][0]["implementation_binding"] = {
        "module": "worldzero.expected",
        "symbol": "demand_response",
    }
    topology = CausalTopologyV2.model_validate(raw)
    payload = coverage_payload()
    payload["topology_id"] = topology.topology_id
    payload["topology_digest"] = topology.digest()
    payload["bindings"][0].update({
        "topology_object_id": "DEMAND_RESPONSE",
        "module": "worldzero.wrong",
        "symbol": "demand_response",
    })
    coverage = ImplementationCoverageV1.model_validate(payload)
    with pytest.raises(ValueError, match="declared implementation binding"):
        validate_coverage(topology, coverage)
