"""Generate deterministic World Zero cohort-population derived artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from worldzero.data import (
    DatasetAdmissionStatus,
    extract_macroregion_cohort_population_bytes,
    load_age_cohort_manifest,
    load_dataset_manifest,
    render_cohort_population_csv,
    verify_payload_digest,
)
from worldzero.data.wpp_age5 import validate_wpp_age5_mapping_compatibility
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import load_region_mapping_manifest

RAW_MANIFEST = Path("data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml")
MAPPING_SOURCE_MANIFEST = Path(
    "data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml"
)
COHORT_MANIFEST = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")
REGION_MANIFEST = Path("regions/WZ_MACROREGION_V0.yaml")
REGION_MAPPING = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")


def generate(raw_path: Path, *, year: int, output_path: Path) -> dict[str, object]:
    raw_manifest = load_dataset_manifest(RAW_MANIFEST)
    mapping_source_manifest = load_dataset_manifest(MAPPING_SOURCE_MANIFEST)
    if raw_manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
        raise ValueError("raw WPP source manifest must be ADMITTED")
    if raw_manifest.content_length_bytes is None:
        raise ValueError("admitted raw WPP source manifest must bind content length")
    raw_bytes = raw_path.read_bytes()
    if len(raw_bytes) != raw_manifest.content_length_bytes:
        raise ValueError("raw WPP payload length does not match admitted manifest")
    if not verify_payload_digest(raw_bytes, raw_manifest.content_sha256):
        raise ValueError("raw WPP payload digest does not match admitted manifest")

    region_set = load_region_set_manifest(REGION_MANIFEST).region_set
    mapping = load_region_mapping_manifest(REGION_MAPPING)
    cohort_manifest = load_age_cohort_manifest(COHORT_MANIFEST)
    validate_wpp_age5_mapping_compatibility(
        mapping_source_manifest=mapping_source_manifest,
        age5_manifest=raw_manifest,
        region_mapping=mapping,
    )
    if mapping.target_region_set_version != region_set.version:
        raise ValueError("region mapping and region set versions do not match")

    cut = extract_macroregion_cohort_population_bytes(
        raw_bytes,
        year=year,
        dataset_id=raw_manifest.dataset_id,
        content_sha256=raw_manifest.content_sha256,
        region_mapping=mapping,
        region_set=region_set,
        cohort_manifest=cohort_manifest,
    )
    rendered = render_cohort_population_csv(cut)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rendered)

    return {
        "cohort_set_version": cut.cohort_set_version,
        "output_length_bytes": len(rendered),
        "output_path": output_path.as_posix(),
        "output_sha256": hashlib.sha256(rendered).hexdigest(),
        "region_set_version": cut.region_set_version,
        "source_dataset_id": raw_manifest.dataset_id,
        "source_observation_class": cut.observation_class.value,
        "source_sha256": raw_manifest.content_sha256,
        "total_population_persons": round(cut.total_population),
        "validation_eligible": cut.validation_eligible,
        "year": cut.year,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_path", type=Path)
    parser.add_argument("year", type=int)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    summary = generate(args.raw_path, year=args.year, output_path=args.output_path)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
