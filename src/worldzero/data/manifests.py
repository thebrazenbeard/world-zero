"""Immutable dataset manifests and admission-state guards."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatasetAdmissionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    RIGHTS_TERMS_CHECKED = "RIGHTS_TERMS_CHECKED"
    SCHEMA_MAPPED = "SCHEMA_MAPPED"
    QUALITY_CHECKED = "QUALITY_CHECKED"
    ADMITTED = "ADMITTED"


_ADMISSION_RANK = {status: index for index, status in enumerate(DatasetAdmissionStatus)}


class DatasetManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_id: Literal["WORLD_ZERO_DATASET_MANIFEST_V1"]
    dataset_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    product: str = Field(min_length=1)
    release_date: date
    retrieved_at: datetime
    source_url: str = Field(min_length=1)
    license: str = Field(min_length=1)
    geography: str = Field(min_length=1)
    time_coverage: str = Field(min_length=1)
    frequency: str = Field(min_length=1)
    units: str = Field(min_length=1)
    transformations: tuple[str, ...]
    missing_data_policy: str = Field(min_length=1)
    uncertainty: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_length_bytes: int | None = Field(default=None, ge=1)
    source_http_status: int | None = Field(default=None, ge=100, le=599)
    source_content_type: str | None = None
    source_last_modified: datetime | None = None
    source_etag: str | None = None
    transform_code_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    rights_terms_checked_at: datetime | None = None
    rights_terms_summary: str | None = None
    schema_mapping_id: str | None = None
    quality_report_id: str | None = None
    admission_record_id: str | None = None
    admission_status: DatasetAdmissionStatus = DatasetAdmissionStatus.CANDIDATE
    supersedes_dataset_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_admission_evidence(self) -> DatasetManifest:
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        rank = _ADMISSION_RANK[self.admission_status]
        rights_rank = _ADMISSION_RANK[DatasetAdmissionStatus.RIGHTS_TERMS_CHECKED]
        schema_rank = _ADMISSION_RANK[DatasetAdmissionStatus.SCHEMA_MAPPED]
        quality_rank = _ADMISSION_RANK[DatasetAdmissionStatus.QUALITY_CHECKED]
        admitted_rank = _ADMISSION_RANK[DatasetAdmissionStatus.ADMITTED]
        if rank >= rights_rank and (
            self.rights_terms_checked_at is None or not self.rights_terms_summary
        ):
            raise ValueError("RIGHTS_TERMS_CHECKED requires rights-review evidence")
        if rank >= schema_rank and not self.schema_mapping_id:
            raise ValueError("SCHEMA_MAPPED requires schema_mapping_id")
        if rank >= quality_rank and not self.quality_report_id:
            raise ValueError("QUALITY_CHECKED requires quality_report_id")
        if rank >= admitted_rank and not self.admission_record_id:
            raise ValueError("ADMITTED requires admission_record_id")
        return self


def verify_payload_digest(payload: bytes, expected_sha256: str) -> bool:
    if len(expected_sha256) != 64:
        raise ValueError("expected SHA-256 must contain 64 hex characters")
    try:
        int(expected_sha256, 16)
    except ValueError as exc:
        raise ValueError("expected SHA-256 must be hexadecimal") from exc
    return hashlib.sha256(payload).hexdigest() == expected_sha256.lower()


def load_dataset_manifest(path: Path) -> DatasetManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("dataset manifest must be a mapping")
    return DatasetManifest.model_validate(payload)
