from pathlib import Path

from worldzero.data.manifests import DatasetAdmissionStatus, load_dataset_manifest
from worldzero.models.bindings import load_baseline_data_bundle_manifest
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


def test_raw_total_source_admission_is_not_the_runtime_binding():
    source = load_dataset_manifest(MANIFEST)
    scenario = load_scenario_manifest(Path("scenarios/2026_baseline.yaml"))
    bundle = load_baseline_data_bundle_manifest(
        Path("data/bundles/WORLD_ZERO_2026_BASELINE_DATA_V0.yaml")
    )

    assert source.admission_status is DatasetAdmissionStatus.ADMITTED
    assert scenario.status == "EXECUTABLE"
    assert scenario.data_manifest_id == bundle.data_manifest_id
    assert scenario.parameter_set_id == "WORLD_ZERO_2026_PROVISIONAL_EXECUTION_V1"
    binding = bundle.binding_by_role["POPULATION_TOTAL"]
    assert binding.dataset_id == "wz-wpp2024-macroregion-population-2026-v1"
    assert binding.dataset_id != source.dataset_id
