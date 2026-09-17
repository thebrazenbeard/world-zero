import importlib
import importlib.util

import pytest


def _topology():
    if importlib.util.find_spec("worldzero.science.topology") is None:
        pytest.fail("worldzero.science.topology is not implemented")
    return importlib.import_module("worldzero.science.topology")


def minimal_payload():
    import json
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_joint_relation_preserves_multi_input_semantics():
    module = _topology()
    topology = module.CausalTopologyV2.model_validate(minimal_payload())
    assert topology.relations[0].inputs == ("SCARCITY", "INCOME", "INVENTORY")
    assert topology.relations[0].outputs == ("DEMAND",)


def test_topology_rejects_missing_input_node():
    module = _topology()
    payload = minimal_payload()
    payload["relations"][0]["inputs"] = ["DOES_NOT_EXIST"]
    with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
        module.CausalTopologyV2.model_validate(payload)


def test_topology_rejects_missing_kill_test_reference():
    module = _topology()
    payload = minimal_payload()
    payload["relations"][0]["kill_test_ids"] = ["DOES_NOT_EXIST"]
    with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
        module.CausalTopologyV2.model_validate(payload)


def test_topology_contract_has_no_self_referential_source_commit():
    module = _topology()
    assert "source_commit" not in module.CausalTopologyV2.model_fields


def test_topology_digest_changes_when_functional_class_changes():
    module = _topology()
    original = module.CausalTopologyV2.model_validate(minimal_payload())
    changed_payload = minimal_payload()
    changed_payload["relations"][0]["functional_form_class"] = "THRESHOLD"
    changed = module.CausalTopologyV2.model_validate(changed_payload)
    assert original.digest() != changed.digest()


def test_duplicate_node_ids_are_rejected():
    module = _topology()
    payload = minimal_payload()
    payload["nodes"].append(dict(payload["nodes"][0]))
    with pytest.raises(ValueError, match="duplicate node"):
        module.CausalTopologyV2.model_validate(payload)
