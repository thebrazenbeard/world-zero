"""Exact-source adapter and frozen-fixture helpers for the World3 control subject."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ReferenceRuntimeError(RuntimeError):
    """Raised when the external World3 reference cannot be trusted or executed."""


@dataclass(frozen=True, slots=True)
class BaselineTrajectory:
    time: tuple[float, ...]
    population: tuple[float, ...]
    resource_fraction: tuple[float, ...]
    food_per_capita: tuple[float, ...]
    industrial_output_per_capita: tuple[float, ...]
    pollution_index: tuple[float, ...]

    def __post_init__(self) -> None:
        series = self._series()
        lengths = {len(values) for values in series.values()}
        if lengths != {len(self.time)} or not self.time:
            raise ValueError("all trajectory series must have the same non-zero length")
        for name, values in series.items():
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"trajectory series {name} contains non-finite values")
        if not all(math.isfinite(value) for value in self.time):
            raise ValueError("trajectory time contains non-finite values")
        if any(b <= a for a, b in zip(self.time, self.time[1:], strict=False)):
            raise ValueError("trajectory time must be strictly increasing")

    def _series(self) -> dict[str, tuple[float, ...]]:
        return {
            "population": self.population,
            "resource_fraction": self.resource_fraction,
            "food_per_capita": self.food_per_capita,
            "industrial_output_per_capita": self.industrial_output_per_capita,
            "pollution_index": self.pollution_index,
        }


@dataclass(frozen=True, slots=True)
class PyWorld3Runtime:
    python_executable: Path
    source_root: Path
    expected_commit: str

    def verify(self) -> None:
        if not self.python_executable.is_file():
            raise ReferenceRuntimeError("reference Python executable does not exist")
        if not self.source_root.is_dir():
            raise ReferenceRuntimeError("reference source root does not exist")
        if re.fullmatch(r"[0-9a-f]{40,64}", self.expected_commit) is None:
            raise ReferenceRuntimeError("expected reference commit is not a Git object id")
        try:
            actual = subprocess.check_output(
                ["git", "-C", str(self.source_root), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.STDOUT,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ReferenceRuntimeError("unable to read reference source commit") from exc
        if actual != self.expected_commit:
            raise ReferenceRuntimeError(
                f"reference commit mismatch: expected {self.expected_commit}, got {actual}"
            )


_BRIDGE = r"""
import json
import sys
from pyworld3 import World3

cfg = json.loads(sys.argv[1])
w = World3(
    year_min=cfg["year_min"], year_max=cfg["year_max"], dt=cfg["dt"],
    pyear=cfg["pyear"], iphst=cfg["iphst"]
)
w.init_world3_constants()
w.init_world3_variables()
w.set_world3_table_functions()
w.set_world3_delay_functions(method="euler")
w.run_world3(fast=False)
print(json.dumps({
    "time": [float(v) for v in w.time],
    "population": [float(v) for v in w.pop],
    "resource_fraction": [float(v) for v in w.nrfr],
    "food_per_capita": [float(v) for v in w.fpc],
    "industrial_output_per_capita": [float(v) for v in w.iopc],
    "pollution_index": [float(v) for v in w.ppolx],
}, separators=(",", ":")))
"""


def _trajectory_from_payload(payload: dict[str, list[float]]) -> BaselineTrajectory:
    return BaselineTrajectory(
        time=tuple(map(float, payload["time"])),
        population=tuple(map(float, payload["population"])),
        resource_fraction=tuple(map(float, payload["resource_fraction"])),
        food_per_capita=tuple(map(float, payload["food_per_capita"])),
        industrial_output_per_capita=tuple(map(float, payload["industrial_output_per_capita"])),
        pollution_index=tuple(map(float, payload["pollution_index"])),
    )


def run_world3_reference(
    runtime: PyWorld3Runtime,
    *,
    year_min: float = 1900.0,
    year_max: float = 2100.0,
    dt: float = 0.5,
    pyear: float = 1975.0,
    iphst: float = 1940.0,
) -> BaselineTrajectory:
    runtime.verify()
    config = {
        "year_min": year_min,
        "year_max": year_max,
        "dt": dt,
        "pyear": pyear,
        "iphst": iphst,
    }
    env = os.environ.copy()
    prior_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(runtime.source_root)
    if prior_pythonpath:
        env["PYTHONPATH"] += os.pathsep + prior_pythonpath
    env.setdefault("MPLBACKEND", "Agg")
    try:
        completed = subprocess.run(
            [str(runtime.python_executable), "-c", _BRIDGE, json.dumps(config)],
            cwd=runtime.source_root,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        detail = getattr(exc, "stderr", "") or ""
        raise ReferenceRuntimeError(f"reference execution failed: {detail.strip()}") from exc
    return _trajectory_from_payload(payload)


def fixture_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_world3_reference(path: Path) -> BaselineTrajectory:
    columns: dict[str, list[float]] = {
        "time": [],
        "population": [],
        "resource_fraction": [],
        "food_per_capita": [],
        "industrial_output_per_capita": [],
        "pollution_index": [],
    }
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            columns["time"].append(float(row["year"]))
            for name, values in columns.items():
                if name != "time":
                    values.append(float(row[name]))
    return _trajectory_from_payload(columns)


def trajectory_error(actual: BaselineTrajectory, expected: BaselineTrajectory) -> float:
    if len(actual.time) != len(expected.time):
        raise ValueError("trajectory lengths differ")
    if any(abs(a - b) > 1e-12 for a, b in zip(actual.time, expected.time, strict=True)):
        raise ValueError("trajectory time grids differ")
    errors: list[float] = []
    for name, expected_values in expected._series().items():
        actual_values = actual._series()[name]
        scale = max(1e-12, max(abs(value) for value in expected_values))
        errors.extend(abs(a - b) / scale for a, b in zip(actual_values, expected_values, strict=True))
    return max(errors, default=0.0)
