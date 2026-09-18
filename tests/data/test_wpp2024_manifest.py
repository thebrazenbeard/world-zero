from pathlib import Path

from worldzero.data.manifests import DatasetAdmissionStatus, load_dataset_manifest
from worldzero.models.scenarios import load_scenario_manifest

MANIFEST = Path("data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml")


def test_wpp2024_raw_source_manifest_is_exact_and_admitted():
    manifest = load_dataset_manifest(MANIFEST)
    assert manifest.admission_status is DatasetAdmissionStatus.ADMITTED
    assert manifest.dataset_id == "un-wpp-2024-demographic-indicators-medium-v1"
    assert manifest.content_sha256 == (
        "286ac36bb1415e2e1ade03acfef0a29f0e4c087e2f78e38c48f50c5df89082bc"
    )
    assert manifest.content_length_bytes == 16_557_272
    assert manifest.ingest_code_commit == "644cd4f70b39176a987de196affa9b7c2763e780"
    assert manifest.transformations == ()
    assert manifest.transform_code_commit is None


def test_admitted_wpp_source_does_not_auto_bind_2026_scenario():
    scenario = load_scenario_manifest(Path("scenarios/2026_baseline.yaml"))
    assert scenario.status == "DATA_BINDING_REQUIRED"
    assert scenario.data_manifest_id is None
    assert scenario.parameter_set_id is None
    assert not scenario.executable
