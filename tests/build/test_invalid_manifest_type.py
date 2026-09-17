import json
from pathlib import Path


def test_manifest_type_error_is_reported_as_invalid_manifest(tmp_path: Path):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    (wheelhouse / "MANIFEST.json").write_text(json.dumps([]), encoding="utf-8")

    from tools.verify_wheelhouse import verify_wheelhouse

    result = verify_wheelhouse(wheelhouse)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_INVALID_MANIFEST"
