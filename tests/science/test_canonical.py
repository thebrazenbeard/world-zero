import math

import pytest

from worldzero.science.canonical import canonical_json_bytes, content_digest


def test_mapping_key_order_does_not_change_digest():
    assert content_digest({"b": 2, "a": 1}) == content_digest({"a": 1, "b": 2})


def test_semantic_change_changes_digest():
    assert content_digest({"kind": "OBSERVED"}) != content_digest({"kind": "INFERRED"})


def test_list_order_is_preserved():
    assert content_digest([1, 2]) != content_digest([2, 1])


def test_utf8_is_not_ascii_escaped():
    assert canonical_json_bytes({"label": "é"}) == b'{"label":"\xc3\xa9"}'


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_numbers_are_rejected(value):
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": value})


def test_non_string_mapping_keys_are_rejected():
    with pytest.raises(TypeError, match="string keys"):
        canonical_json_bytes({1: "ambiguous"})


def test_model_dump_objects_preserve_none_fields():
    class FakeModel:
        def model_dump(self, *, mode, exclude_none):
            assert mode == "json"
            assert exclude_none is False
            return {"present": 1, "missing": None}

    assert canonical_json_bytes(FakeModel()) == b'{"missing":null,"present":1}'


def test_digest_is_lowercase_sha256_hex():
    digest = content_digest({"a": 1})
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)
