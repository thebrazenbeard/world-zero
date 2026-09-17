from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "wheelhouse"


def _verifier_module():
    path = Path("tools/verify_wheelhouse.py")
    assert path.exists(), "tools/verify_wheelhouse.py is not implemented yet"
    spec = importlib.util.spec_from_file_location("verify_wheelhouse", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "wheelhouse"
    shutil.copytree(FIXTURE, target)
    return target


def test_verified_manifest_accepts_matching_artifact(tmp_path):
    module = _verifier_module()
    target = _copy_fixture(tmp_path)
    result = module.verify_wheelhouse(target)
    assert result.ok is True
    assert result.code == "PASS"


def test_missing_artifact_fails_closed(tmp_path):
    module = _verifier_module()
    target = _copy_fixture(tmp_path)
    (target / "demo-1.0-py3-none-any.whl").unlink()
    result = module.verify_wheelhouse(target)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_INCOMPLETE"


def test_hash_mismatch_fails_closed(tmp_path):
    module = _verifier_module()
    target = _copy_fixture(tmp_path)
    (target / "demo-1.0-py3-none-any.whl").write_bytes(b"tampered")
    result = module.verify_wheelhouse(target)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_TAMPERED_OR_DRIFTED"


def test_undeclared_wheel_fails_closed(tmp_path):
    module = _verifier_module()
    target = _copy_fixture(tmp_path)
    (target / "extra-1.0-py3-none-any.whl").write_bytes(b"extra")
    result = module.verify_wheelhouse(target)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_UNDECLARED_ARTIFACT"
