from pathlib import Path

import pytest

from worldzero.models.scenarios import ScenarioManifest, load_scenario_manifest


def test_world3_compatibility_manifest_is_control_only_and_bound_to_frozen_fixture():
    manifest = load_scenario_manifest(Path("scenarios/world3_compatibility.yaml"))
    assert manifest.scenario_class == "EXTERNAL_CONTROL"
    assert manifest.status == "CONTROL_ONLY"
    assert manifest.reference_sha256 == (
        "31d3f493e942e3f0eadf8828bf51ec968745e19b12399dc382138e89a67a2d68"
    )


def test_2026_baseline_is_executable_with_explicit_bound_inputs():
    manifest = load_scenario_manifest(Path("scenarios/2026_baseline.yaml"))
    assert manifest.scenario_class == "NATIVE_BASELINE"
    assert manifest.status == "EXECUTABLE"
    assert manifest.executable
    assert manifest.data_manifest_id == "WORLD_ZERO_2026_BASELINE_DATA_V0"
    assert manifest.parameter_set_id == "WORLD_ZERO_2026_PROVISIONAL_EXECUTION_V1"


def test_native_executable_status_requires_data_and_parameter_bindings():
    with pytest.raises(ValueError, match="data_manifest_id"):
        ScenarioManifest(
            schema_version="WORLD_ZERO_SCENARIO_V1",
            scenario_id="bad",
            scenario_class="NATIVE_BASELINE",
            status="EXECUTABLE",
            start=2026.0,
            stop=2030.0,
            dt=0.25,
            region_set_version="WZ_MACROREGION_V0",
        )
