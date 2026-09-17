"""Deterministic JSON serialization and SHA-256 content identities."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def _normalize(value: Any) -> Any:
    """Convert supported contract objects into a canonical JSON-compatible form."""
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _normalize(model_dump(mode="json", exclude_none=False))

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON mappings require string keys")
            normalized[key] = _normalize(item)
        return normalized

    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]

    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for a scientific contract value."""
    normalized = _normalize(value)
    text = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def content_digest(value: Any) -> str:
    """Return the lowercase SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
