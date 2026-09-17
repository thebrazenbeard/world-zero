import importlib
import importlib.util

import pytest

from tests.science.test_topology_v2 import minimal_payload
from worldzero.science.topology import CausalTopologyV2


def _coverage():
    if importlib.util.find_spec("worldzero.science.implementation_coverage") is None:
        pytest.fail("worldzero.science.implementation_coverage is not implemented")
    return importlib.import_module("worldzero.science.implementation_coverage")


def topology():
    return CausalTopologyV2.model_validate(minimal_payload())


def valid_coverage(module):
    t = topology()
    return module.ImplementationCoverage(
        schema_version="IMPLEMENTATION_COVERAGE_V1",
        coverage_id="COVERAGE_TEST",
        topology_id=t.topology_id,
        topology_digest=t.digest(),
        source_commit="a" * 40,
        bindings=(
            module.ImplementationBinding(
                topology_object_id="DEMAND_RESPONSE",
                object_kind="RELATION",
                module="worldzero.sectors.market",
                symbol="demand_response",
                binding_status="BOUND",
                micro_test_ids=("TEST_DEMAND_RESPONSE_LIMIT",),
            ),
        ),
        coverage_status="PASS",
    )


def test_active_relation_without_code_binding_fails():
    module = _coverage()
    t = topology()
    coverage = valid_coverage(module).model_copy(update={"bindings": ()})
    with pytest.raises(ValueError, match="DEMAND_RESPONSE"):
        module.validate_coverage(t, coverage)


def test_undeclared_runtime_relation_prevents_pass():
    module = _coverage()
    payload = valid_coverage(module).model_dump(mode="json")
    payload["undeclared_runtime_relations"] = ["HIDDEN_COUPLING"]
    with pytest.raises(ValueError, match="undeclared"):
        module.ImplementationCoverage.model_validate(payload)


def test_endogenous_relation_requires_micro_test():
    module = _coverage()
    t = topology()
    coverage = valid_coverage(module)
    bad_binding = coverage.bindings[0].model_copy(update={"micro_test_ids": ()})
    bad = coverage.model_copy(update={"bindings": (bad_binding,), "coverage_status": "INCOMPLETE"})
    with pytest.raises(ValueError, match="micro-test"):
        module.validate_coverage(t, bad)


def test_valid_coverage_passes_exact_reconciliation():
    module = _coverage()
    coverage = valid_coverage(module)
    result = module.validate_coverage(topology(), coverage)
    assert result.coverage_status == "PASS"
