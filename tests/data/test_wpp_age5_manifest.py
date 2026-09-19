from pathlib import Path

from worldzero.data.manifests import DatasetAdmissionStatus, load_dataset_manifest
from worldzero.models.bindings import load_baseline_data_bundle_manifest
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


def test_raw_age_source_admission_is_not_the_runtime_binding():
    source = load_dataset_manifest(MANIFEST)
    scenario = load_scenario_manifest(Path("scenarios/2026_baseline.yaml"))
    bundle = load_baseline_data_bundle_manifest(
        Path("data/bundles/WORLD_ZERO_2026_BASELINE_DATA_V0.yaml")
    )

    assert source.admission_status is DatasetAdmissionStatus.ADMITTED
    assert scenario.status == "EXECUTABLE"
    assert scenario.data_manifest_id == bundle.data_manifest_id
    assert scenario.parameter_set_id == "WORLD_ZERO_2026_PROVISIONAL_EXECUTION_V1"
    binding = bundle.binding_by_role["POPULATION_COHORT"]
    assert binding.dataset_id == "wz-wpp2024-macroregion-cohort-population-2026-v1"
    assert binding.dataset_id != source.dataset_id
