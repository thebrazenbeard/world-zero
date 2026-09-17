import math

import pytest
from pydantic import BaseModel

from worldzero.science.canonical import canonical_json_bytes, content_digest


class ExampleModel(BaseModel):
    b: int
    a: int | None = None


def test_mapping_key_order_does_not_change_digest():
    assert content_digest({"b": 2, "a": 1}) == content_digest({"a": 1, "b": 2})


def test_semantic_change_changes_digest():
    assert content_digest({"kind": "OBSERVED"}) != content_digest({"kind": "INFERRED"})


def test_list_order_is_preserved():
    assert content_digest([1, 2]) != content_digest([2, 1])


def test_pydantic_none_is_not_silently_dropped():
    payload = canonical_json_bytes(ExampleModel(b=2))
    assert payload == b'{"a":null,"b":2}'


def test_non_finite_numbers_are_rejected():
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": math.nan})
