import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

from worldzero.baselines.world3_reference import (
    PyWorld3Runtime,
    ReferenceRuntimeError,
    fixture_sha256,
    load_frozen_world3_reference,
    run_world3_reference,
    trajectory_error,
)

FIXTURE = Path(__file__).parent / "fixtures" / "world3_standard_run.csv"
FIXTURE_SHA256 = "31d3f493e942e3f0eadf8828bf51ec968745e19b12399dc382138e89a67a2d68"


def test_frozen_fixture_has_exact_identity_and_shape():
    trajectory = load_frozen_world3_reference(FIXTURE)
    assert fixture_sha256(FIXTURE) == FIXTURE_SHA256
    assert len(trajectory.time) == 401
    assert trajectory.time[0] == 1900.0
    assert trajectory.time[-1] == 2100.0


def test_trajectory_error_is_zero_for_identical_trajectory():
    trajectory = load_frozen_world3_reference(FIXTURE)
    assert trajectory_error(trajectory, trajectory) == 0.0


def _fake_reference_source() -> str:
    return '''
class World3:
    def __init__(self, year_min=1900, year_max=2100, dt=0.5, pyear=1975, iphst=1940):
        self.year_min = year_min
        self.year_max = year_max
        self.dt = dt
    def init_world3_constants(self): pass
    def init_world3_variables(self): pass
    def set_world3_table_functions(self): pass
    def set_world3_delay_functions(self, method="euler"): pass
    def run_world3(self, fast=False):
        self.time = [self.year_min, self.year_min + self.dt, self.year_max]
        self.pop = [1.0, 2.0, 3.0]
        self.nrfr = [1.0, 0.9, 0.8]
        self.fpc = [10.0, 11.0, 12.0]
        self.iopc = [20.0, 21.0, 22.0]
        self.ppolx = [0.1, 0.2, 0.3]
'''


def _make_fake_runtime(tmp_path: Path) -> PyWorld3Runtime:
    root = tmp_path / "pyworld3-reference"
    package = root / "pyworld3"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(_fake_reference_source(), encoding="utf-8")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "World Zero Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "pyworld3/__init__.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "fake reference"], cwd=root, check=True, capture_output=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return PyWorld3Runtime(
        python_executable=Path(sys.executable),
        source_root=root,
        expected_commit=commit,
    )


def test_external_reference_adapter_executes_exact_bound_source(tmp_path: Path):
    runtime = _make_fake_runtime(tmp_path)
    trajectory = run_world3_reference(runtime, year_min=1900, year_max=1901, dt=0.5)
    assert trajectory.time == (1900.0, 1900.5, 1901.0)
    assert trajectory.population == (1.0, 2.0, 3.0)


def test_external_reference_adapter_rejects_source_commit_drift(tmp_path: Path):
    runtime = _make_fake_runtime(tmp_path)
    drifted = dataclasses.replace(runtime, expected_commit="0" * 40)
    with pytest.raises(ReferenceRuntimeError, match="commit mismatch"):
        run_world3_reference(drifted, year_min=1900, year_max=1901, dt=0.5)
