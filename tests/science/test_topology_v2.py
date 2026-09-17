import json
from pathlib import Path

import pytest

from worldzero.science.topology import CausalTopologyV2


FIXTURE = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"


def minimal_payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_joint_relation_preserves_multi_input_semantics():
    topology = CausalTopologyV2.model_validate(minimal_payload())
    assert topology.relations[0].inputs == ("SCARCITY", "INCOME", "INVENTORY")


def test_topology_rejects_missing_input_node():
    payload = minimal_payload()
    payload["relations"][0]["inputs"] = ["DOES_NOT_EXIST"]
    with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
        CausalTopologyV2.model_validate(payload)


def test_topology_contract_has_no_self_referential_source_commit():
    assert "source_commit" not in CausalTopologyV2.model_fields
    payload = minimal_payload()
    payload["source_commit"] = "deadbeef"
    with pytest.raises(ValueError):
        CausalTopologyV2.model_validate(payload)


def test_duplicate_node_id_is_rejected():
    payload = minimal_payload()
    payload["nodes"].append(dict(payload["nodes"][0]))
    with pytest.raises(ValueError, match="duplicate node ID"):
        CausalTopologyV2.model_validate(payload)


def test_duplicate_relation_id_is_rejected():
    payload = minimal_payload()
    payload["relations"].append(dict(payload["relations"][0]))
    with pytest.raises(ValueError, match="duplicate relation ID"):
        CausalTopologyV2.model_validate(payload)


def test_missing_kill_test_reference_is_rejected():
    payload = minimal_payload()
    payload["relations"][0]["kill_test_ids"] = ["KT_MISSING"]
    with pytest.raises(ValueError, match="KT_MISSING"):
        CausalTopologyV2.model_validate(payload)


def test_missing_local_rival_relation_is_rejected():
    payload = minimal_payload()
    payload["relations"][0]["rival_relation_ids"] = ["MISSING_RIVAL"]
    with pytest.raises(ValueError, match="MISSING_RIVAL"):
        CausalTopologyV2.model_validate(payload)


def test_external_rival_relation_reference_is_allowed():
    payload = minimal_payload()
    payload["relations"][0]["rival_relation_ids"] = ["F3_NET_ENERGY_MATERIAL:ENERGY_PRICE_RESPONSE"]
    topology = CausalTopologyV2.model_validate(payload)
    assert topology.relations[0].rival_relation_ids == (
        "F3_NET_ENERGY_MATERIAL:ENERGY_PRICE_RESPONSE",
    )


def test_empty_relation_inputs_are_rejected():
    payload = minimal_payload()
    payload["relations"][0]["inputs"] = []
    with pytest.raises(ValueError):
        CausalTopologyV2.model_validate(payload)


def test_topology_digest_changes_when_functional_class_changes():
    topology = CausalTopologyV2.model_validate(minimal_payload())
    changed = topology.model_copy(deep=True)
    changed.relations[0].functional_form_class = "THRESHOLD"
    assert changed.digest() != topology.digest()


def test_equivalent_mapping_key_order_has_same_topology_digest():
    payload = minimal_payload()
    topology_a = CausalTopologyV2.model_validate(payload)
    topology_b = CausalTopologyV2.model_validate(dict(reversed(list(payload.items()))))
    assert topology_a.digest() == topology_b.digest()
