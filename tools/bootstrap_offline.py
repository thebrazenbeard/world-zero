from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv

from tools.verify_wheelhouse import verify_wheelhouse


def build_pip_install_command(
    wheelhouse: Path,
    requirements_lock: Path,
    python_executable: str,
) -> list[str]:
    return [
        python_executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--no-cache-dir",
        "--find-links",
        str(wheelhouse),
        "--requirement",
        str(requirements_lock),
    ]


def _venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def bootstrap_offline(wheelhouse: Path, venv_path: Path) -> Path:
    result = verify_wheelhouse(wheelhouse)
    if not result.ok:
        raise RuntimeError(f"wheelhouse verification failed: {result.code} {result.details}")
    requirements_lock = wheelhouse / "requirements.lock"
    if not requirements_lock.is_file():
        raise RuntimeError("wheelhouse requirements.lock is missing")
    if venv_path.exists() and any(venv_path.iterdir()):
        raise RuntimeError(f"target virtual environment must be empty: {venv_path}")

    venv.EnvBuilder(with_pip=True, clear=False).create(venv_path)
    python_executable = _venv_python(venv_path)
    env = os.environ.copy()
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    subprocess.run(
        build_pip_install_command(wheelhouse, requirements_lock, str(python_executable)),
        check=True,
        env=env,
    )
    return python_executable


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap World Zero from a local wheelhouse")
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--venv", type=Path, required=True)
    args = parser.parse_args()
    python_executable = bootstrap_offline(args.wheelhouse, args.venv)
    print(python_executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
