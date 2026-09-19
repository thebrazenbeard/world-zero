import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from worldzero.data.derived import (
    DerivedDatasetManifest,
    load_derived_dataset_manifest,
)
from worldzero.data.observations import ObservationClass

MANIFEST_2023 = Path("data/manifests/WZ_WPP_2024_MACROREGION_POPULATION_2023_V1.yaml")
MANIFEST_2026 = Path("data/manifests/WZ_WPP_2024_MACROREGION_POPULATION_2026_V1.yaml")


def _verify_output(path: Path, expected_sha256: str, expected_bytes: int) -> None:
    payload = path.read_bytes()
    assert len(payload) == expected_bytes
    assert hashlib.sha256(payload).hexdigest() == expected_sha256


def test_2023_derived_manifest_is_validation_eligible_and_exact():
    manifest = load_derived_dataset_manifest(MANIFEST_2023)
    assert manifest.source_observation_class is ObservationClass.OFFICIAL_ESTIMATE
    assert manifest.validation_eligible
    assert manifest.cohort_set_version is None
    assert manifest.transform_code_commit == ("9956829a326b533670dd01eaa9cb4d1ce852fcb3")
    _verify_output(
        Path(manifest.output_path),
        manifest.output_sha256,
        manifest.output_length_bytes,
    )


def test_2026_derived_manifest_is_bridge_only_and_exact():
    manifest = load_derived_dataset_manifest(MANIFEST_2026)
    assert manifest.source_observation_class is ObservationClass.PROJECTION
    assert not manifest.validation_eligible
    assert manifest.cohort_set_version is None
    _verify_output(
        Path(manifest.output_path),
        manifest.output_sha256,
        manifest.output_length_bytes,
    )


def test_derived_manifest_accepts_explicit_cohort_set_binding():
    manifest = load_derived_dataset_manifest(MANIFEST_2023)
    payload = manifest.model_dump(mode="python")
    payload["cohort_set_version"] = "WZ_AGE_COHORT_V0"
    rebound = DerivedDatasetManifest.model_validate(payload)
    assert rebound.cohort_set_version == "WZ_AGE_COHORT_V0"


def test_projection_derived_manifest_cannot_be_validation_eligible():
    manifest = load_derived_dataset_manifest(MANIFEST_2026)
    payload = manifest.model_dump(mode="python")
    payload["validation_eligible"] = True
    with pytest.raises(ValidationError, match="cannot be validation eligible"):
        DerivedDatasetManifest.model_validate(payload)
