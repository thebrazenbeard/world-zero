import json
from pathlib import Path

import pytest

from worldzero.science.topology import CausalTopologyV2

FIXTURE = Path(__file__).parent / "fixtures" / "minimal_topology_v2.json"


def minimal_payload() -> dict:
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


def test_duplicate_node_id_is_rejected():
    payload = minimal_payload()
    payload["nodes"].append(dict(payload["nodes"][0]))
    with pytest.raises(ValueError, match="duplicate node"):
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


def test_external_rival_uses_family_colon_relation_syntax():
    payload = minimal_payload()
    payload["relations"][0]["rival_relation_ids"] = ["F3_NET_ENERGY_MATERIAL:ENERGY_LIMIT"]
    topology = CausalTopologyV2.model_validate(payload)
    assert topology.relations[0].rival_relation_ids == (
        "F3_NET_ENERGY_MATERIAL:ENERGY_LIMIT",
    )


def test_malformed_external_rival_is_rejected():
    payload = minimal_payload()
    payload["relations"][0]["rival_relation_ids"] = [":ENERGY_LIMIT"]
    with pytest.raises(ValueError, match="rival"):
        CausalTopologyV2.model_validate(payload)


def test_topology_digest_changes_when_functional_class_changes():
    topology = CausalTopologyV2.model_validate(minimal_payload())
    changed = topology.model_copy(deep=True)
    changed.relations[0].functional_form_class = "THRESHOLD"
    assert changed.digest() != topology.digest()
