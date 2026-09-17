import json
from pathlib import Path

import pytest

from worldzero.science.implementation_coverage import (
    ImplementationBinding,
    ImplementationCoverage,
    validate_coverage,
)
from worldzero.science.topology import (
    CausalTopologyV2,
)
from worldzero.science.topology import (
    ImplementationBinding as TopologyImplementationBinding,
)

FIXTURE = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"


def topology():
    return CausalTopologyV2.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def valid_coverage(topo):
    return ImplementationCoverage(
        schema_version="IMPLEMENTATION_COVERAGE_V1",
        coverage_id="COV_TEST",
        topology_id=topo.topology_id,
        topology_digest=topo.digest(),
        source_commit="a" * 40,
        bindings=(
            ImplementationBinding(
                topology_object_id="DEMAND_RESPONSE",
                object_kind="RELATION",
                module="worldzero.models.market",
                symbol="demand_response",
                binding_status="BOUND",
                micro_test_ids=("TEST_DEMAND_RESPONSE_POLARITY",),
            ),
        ),
        coverage_status="PASS",
    )


def test_active_relation_without_code_binding_fails():
    topo = topology()
    coverage = valid_coverage(topo).model_copy(update={"bindings": ()}, deep=True)
    with pytest.raises(ValueError, match="DEMAND_RESPONSE"):
        validate_coverage(topo, coverage)


def test_undeclared_runtime_relation_prevents_pass():
    topo = topology()
    coverage = valid_coverage(topo).model_copy(
        update={"undeclared_runtime_relations": ("HIDDEN_COUPLING",)}, deep=True
    )
    with pytest.raises(ValueError, match="HIDDEN_COUPLING"):
        validate_coverage(topo, coverage)


def test_false_pass_claim_with_diagnostic_defect_is_rejected_at_construction():
    topo = topology()
    with pytest.raises(ValueError, match="PASS"):
        ImplementationCoverage(
            schema_version="IMPLEMENTATION_COVERAGE_V1",
            coverage_id="COV_FALSE_PASS",
            topology_id=topo.topology_id,
            topology_digest=topo.digest(),
            source_commit="a" * 40,
            bindings=(),
            undeclared_runtime_relations=("HIDDEN_COUPLING",),
            coverage_status="PASS",
        )


def test_topology_digest_mismatch_fails():
    topo = topology()
    coverage = valid_coverage(topo).model_copy(update={"topology_digest": "0" * 64}, deep=True)
    with pytest.raises(ValueError, match="digest"):
        validate_coverage(topo, coverage)


def test_endogenous_relation_requires_micro_test():
    topo = topology()
    binding = valid_coverage(topo).bindings[0].model_copy(update={"micro_test_ids": ()})
    coverage = valid_coverage(topo).model_copy(update={"bindings": (binding,)}, deep=True)
    with pytest.raises(ValueError, match="micro-test"):
        validate_coverage(topo, coverage)


def test_duplicate_binding_target_is_rejected():
    topo = topology()
    binding = valid_coverage(topo).bindings[0]
    coverage = valid_coverage(topo).model_copy(update={"bindings": (binding, binding)}, deep=True)
    with pytest.raises(ValueError, match="duplicate binding"):
        validate_coverage(topo, coverage)


def test_unknown_binding_target_is_rejected():
    topo = topology()
    unknown = ImplementationBinding(
        topology_object_id="NOT_DECLARED",
        object_kind="RELATION",
        module="worldzero.models.bad",
        symbol="hidden",
        binding_status="BOUND",
        micro_test_ids=("TEST_HIDDEN",),
    )
    coverage = valid_coverage(topo).model_copy(update={"bindings": (unknown,)}, deep=True)
    with pytest.raises(ValueError, match="NOT_DECLARED"):
        validate_coverage(topo, coverage)


def test_declared_node_implementation_binding_requires_coverage_entry():
    topo = topology().model_copy(deep=True)
    topo.nodes[0].implementation_binding = TopologyImplementationBinding(
        module="worldzero.models.market",
        symbol="scarcity_state",
    )
    coverage = valid_coverage(topo).model_copy(update={"topology_digest": topo.digest()}, deep=True)
    with pytest.raises(ValueError, match="SCARCITY"):
        validate_coverage(topo, coverage)


def test_declared_relation_binding_drift_fails():
    topo = topology().model_copy(deep=True)
    topo.relations[0].implementation_binding = TopologyImplementationBinding(
        module="worldzero.models.market",
        symbol="declared_demand_response",
    )
    binding = valid_coverage(topo).bindings[0].model_copy(
        update={"symbol": "different_runtime_symbol"}
    )
    coverage = valid_coverage(topo).model_copy(
        update={"topology_digest": topo.digest(), "bindings": (binding,)}, deep=True
    )
    with pytest.raises(ValueError, match="binding drift"):
        validate_coverage(topo, coverage)


def test_endogenous_intentionally_external_relation_still_requires_micro_test():
    topo = topology()
    binding = valid_coverage(topo).bindings[0].model_copy(
        update={"binding_status": "INTENTIONALLY_EXTERNAL", "micro_test_ids": ()}
    )
    coverage = valid_coverage(topo).model_copy(update={"bindings": (binding,)}, deep=True)
    with pytest.raises(ValueError, match="micro-test"):
        validate_coverage(topo, coverage)


def test_valid_coverage_passes():
    topo = topology()
    validate_coverage(topo, valid_coverage(topo))


def test_declared_behavioral_contract_drift_fails():
    topo = topology().model_copy(deep=True)
    topo.relations[0].implementation_binding = TopologyImplementationBinding(
        module="worldzero.models.market",
        symbol="demand_response",
        behavioral_contract_id="BC_EXPECTED",
    )
    binding = valid_coverage(topo).bindings[0].model_copy(
        update={"behavioral_contract_id": "BC_WRONG"}
    )
    coverage = valid_coverage(topo).model_copy(
        update={"topology_digest": topo.digest(), "bindings": (binding,)}, deep=True
    )
    with pytest.raises(ValueError, match="binding drift"):
        validate_coverage(topo, coverage)
