from __future__ import annotations

import platform as platform_module
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentIdentity:
    python_implementation: str
    python_version: str
    platform: str
    machine: str
    executable: str


def capture_environment_identity() -> EnvironmentIdentity:
    version = sys.version_info
    return EnvironmentIdentity(
        python_implementation=platform_module.python_implementation(),
        python_version=f"{version.major}.{version.minor}.{version.micro}",
        platform=platform_module.platform(),
        machine=platform_module.machine(),
        executable=sys.executable,
    )
