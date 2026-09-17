import importlib
import importlib.util
import math

import pytest


def _canonical_module():
    if importlib.util.find_spec("worldzero.science.canonical") is None:
        pytest.fail("worldzero.science.canonical is not implemented")
    return importlib.import_module("worldzero.science.canonical")


def test_mapping_key_order_does_not_change_digest():
    content_digest = _canonical_module().content_digest
    assert content_digest({"b": 2, "a": 1}) == content_digest({"a": 1, "b": 2})


def test_semantic_change_changes_digest():
    content_digest = _canonical_module().content_digest
    assert content_digest({"kind": "OBSERVED"}) != content_digest({"kind": "INFERRED"})


def test_list_order_is_semantic():
    content_digest = _canonical_module().content_digest
    assert content_digest(["a", "b"]) != content_digest(["b", "a"])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_numbers_are_rejected(value):
    canonical_json_bytes = _canonical_module().canonical_json_bytes
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": value})
