from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_tool(name: str):
    path = Path("tools") / f"{name}.py"
    assert path.exists(), f"{path} is not implemented yet"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bootstrap_disables_indexes_and_cache():
    module = _load_tool("bootstrap_offline")
    command = module.build_pip_install_command(
        Path("wheelhouse"), Path("wheelhouse/requirements.lock"), "python"
    )
    assert "--no-index" in command
    assert "--no-cache-dir" in command
    assert "--find-links" in command


def test_bundle_builder_requires_binary_artifacts():
    module = _load_tool("build_wheelhouse")
    command = module.build_download_command(
        Path("requirements.txt"), Path("wheelhouse"), "cp312-win_amd64", "python"
    )
    assert "--only-binary=:all:" in command
    assert command[command.index("--platform") + 1] == "win_amd64"
    assert command[command.index("--python-version") + 1] == "3.12"
    assert command[command.index("--abi") + 1] == "cp312"


def test_linux_bundle_target_is_explicit():
    module = _load_tool("build_wheelhouse")
    command = module.build_download_command(
        Path("requirements.txt"), Path("wheelhouse"), "cp312-manylinux_x86_64", "python"
    )
    assert command[command.index("--platform") + 1] == "manylinux_2_17_x86_64"


def test_unknown_bundle_target_is_rejected():
    module = _load_tool("build_wheelhouse")
    try:
        module.build_download_command(
            Path("requirements.txt"), Path("wheelhouse"), "mystery-target", "python"
        )
    except ValueError as exc:
        assert "mystery-target" in str(exc)
    else:
        raise AssertionError("unknown target must fail closed")
