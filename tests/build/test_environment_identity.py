import importlib
import importlib.util


def _buildenv_module():
    spec = importlib.util.find_spec("worldzero.buildenv")
    assert spec is not None, "worldzero.buildenv is not implemented yet"
    return importlib.import_module("worldzero.buildenv")


def test_environment_identity_records_exact_python_version():
    buildenv = _buildenv_module()
    identity = buildenv.capture_environment_identity()
    assert identity.python_version.count(".") >= 2
    assert identity.python_implementation == "CPython"


def test_environment_identity_records_platform_and_machine():
    buildenv = _buildenv_module()
    identity = buildenv.capture_environment_identity()
    assert identity.platform
    assert identity.machine
