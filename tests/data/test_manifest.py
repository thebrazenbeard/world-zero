from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from worldzero.data.manifests import (
    DatasetAdmissionStatus,
    DatasetManifest,
    verify_payload_digest,
)

VALID = {
    "schema_id": "WORLD_ZERO_DATASET_MANIFEST_V1",
    "dataset_id": "wpp-population-2024",
    "provider": "UN DESA Population Division",
    "product": "World Population Prospects 2024",
    "release_date": date(2024, 7, 11),
    "retrieved_at": datetime(2026, 9, 18, tzinfo=UTC),
    "source_url": "https://example.invalid/wpp",
    "license": "Open/public-use terms reviewed",
    "geography": "global country/area coverage",
    "time_coverage": "1950-2023 historical observations",
    "frequency": "annual",
    "units": "persons",
    "transformations": ("country-to-macroregion aggregation v1",),
    "missing_data_policy": "fail closed unless declared source missingness",
    "uncertainty": "provider estimates; revision-sensitive",
    "content_sha256": "a" * 64,
    "transform_code_commit": "b" * 40,
    "rights_terms_checked_at": datetime(2026, 9, 18, tzinfo=UTC),
    "rights_terms_summary": "open/public-use terms reviewed",
    "schema_mapping_id": "WZ_WPP_2024_MAP_V1",
    "quality_report_id": "WZ_WPP_2024_QA_V1",
    "admission_status": DatasetAdmissionStatus.QUALITY_CHECKED,
}


def test_manifest_requires_digest_and_vintage():
    with pytest.raises(ValidationError):
        DatasetManifest(dataset_id="wpp-population", provider="UN DESA")


def test_manifest_rejects_admitted_without_rights_schema_and_quality_gates():
    with pytest.raises(ValidationError, match="ADMITTED"):
        DatasetManifest(**{**VALID, "admission_status": DatasetAdmissionStatus.ADMITTED})


def test_payload_digest_verification_is_exact():
    payload = b"world-zero-test-payload"
    import hashlib

    digest = hashlib.sha256(payload).hexdigest()
    assert verify_payload_digest(payload, digest)
    assert not verify_payload_digest(payload + b"x", digest)
