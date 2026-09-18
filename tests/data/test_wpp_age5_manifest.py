from pathlib import Path

from worldzero.data.manifests import DatasetAdmissionStatus, load_dataset_manifest
from worldzero.models.scenarios import load_scenario_manifest

MANIFEST = Path("data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml")


def test_wpp_age5_raw_source_is_exact_and_admitted():
    manifest = load_dataset_manifest(MANIFEST)
    assert manifest.admission_status is DatasetAdmissionStatus.ADMITTED
    assert manifest.dataset_id == "un-wpp-2024-population-age5-sex-medium-v1"
    assert manifest.content_sha256 == (
        "a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd"
    )
    assert manifest.content_length_bytes == 29_948_947
    assert manifest.ingest_code_commit == "c4fb3c183cb3ea77220c41a91b9640ca4e6664a7"
    assert manifest.transformations == ()
    assert manifest.transform_code_commit is None


def test_age_source_admission_does_not_make_2026_scenario_executable():
    scenario = load_scenario_manifest(Path("scenarios/2026_baseline.yaml"))
    assert scenario.status == "DATA_BINDING_REQUIRED"
    assert not scenario.executable
