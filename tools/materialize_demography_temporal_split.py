"""Materialize a governed pre-2023 initialization / 2023 holdout data split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.manifests import DatasetAdmissionStatus, DatasetManifest, load_dataset_manifest
from worldzero.data.observations import ObservationClass, ObservationSeries
from worldzero.data.wpp2024 import extract_parent_group_midyear_population
from worldzero.data.wpp_age5 import (
    extract_macroregion_cohort_population,
    render_cohort_population_csv,
    validate_wpp_age5_mapping_compatibility,
)
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import (
    aggregate_grouped_observation,
    load_region_mapping_manifest,
)

INITIALIZATION_YEAR = 2022
HOLDOUT_YEAR = 2023
TOTAL_FIELDS = (
    "region_id",
    "year",
    "population_persons",
    "source_observation_class",
    "observation_class",
    "validation_eligible",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verify_raw_file(manifest: DatasetManifest, path: Path) -> None:
    if manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
        raise ValueError("raw source must be ADMITTED")
    payload = path.read_bytes()
    if manifest.content_length_bytes is None:
        raise ValueError("raw source manifest must bind content length")
    if len(payload) != manifest.content_length_bytes:
        raise ValueError("raw source length does not match admitted manifest")
    if _sha256(payload) != manifest.content_sha256:
        raise ValueError("raw source digest does not match admitted manifest")


def render_macroregion_population_csv(
    *,
    source: ObservationSeries,
    aggregated: ObservationSeries,
    region_ids: tuple[str, ...],
    year: int,
) -> bytes:
    """Render deterministic macroregion population rows matching the governed schema."""

    if source.observation_class is not ObservationClass.OFFICIAL_ESTIMATE:
        raise ValueError("temporal validation source must be an official estimate")
    if not source.validation_eligible or not aggregated.validation_eligible:
        raise ValueError("temporal validation source must remain validation eligible")
    if aggregated.observation_class is not ObservationClass.DERIVED:
        raise ValueError("macroregion population output must be DERIVED")
    if aggregated.geography != region_ids:
        raise ValueError("macroregion population order must match frozen region order")
    if aggregated.time != tuple(year for _ in region_ids):
        raise ValueError("macroregion population output must contain exactly one requested year")
    if len(aggregated.values) != len(region_ids):
        raise ValueError("macroregion population output length mismatch")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=TOTAL_FIELDS, lineterminator="\n")
    writer.writeheader()
    for region_id, value in zip(region_ids, aggregated.values, strict=True):
        rounded = round(float(value))
        if value <= 0 or abs(float(value) - rounded) > 0.001:
            raise ValueError("macroregion population must resolve to positive whole persons")
        writer.writerow(
            {
                "region_id": region_id,
                "year": year,
                "population_persons": int(rounded),
                "source_observation_class": source.observation_class.value,
                "observation_class": aggregated.observation_class.value,
                "validation_eligible": "true",
            }
        )
    return buffer.getvalue().encode("utf-8")


def _derive_total(
    *,
    raw_path: Path,
    raw_manifest: DatasetManifest,
    mapping_path: Path,
    regions_path: Path,
    year: int,
    transform_code_commit: str,
) -> bytes:
    mapping = load_region_mapping_manifest(mapping_path)
    regions = load_region_set_manifest(regions_path).region_set
    parent = extract_parent_group_midyear_population(
        raw_path,
        years=(year,),
        dataset_id=raw_manifest.dataset_id,
        content_sha256=raw_manifest.content_sha256,
    )
    aggregated = aggregate_grouped_observation(
        parent,
        mapping=mapping,
        target_region_set=regions,
        output_observable_id="population_midyear_macroregion",
        transform_version="1.0.0",
        transform_code_commit=transform_code_commit,
    )
    return render_macroregion_population_csv(
        source=parent,
        aggregated=aggregated,
        region_ids=regions.ids,
        year=year,
    )


def _derive_cohorts(
    *,
    raw_path: Path,
    raw_manifest: DatasetManifest,
    mapping_source_manifest: DatasetManifest,
    mapping_path: Path,
    regions_path: Path,
    cohorts_path: Path,
    year: int,
) -> bytes:
    mapping = load_region_mapping_manifest(mapping_path)
    regions = load_region_set_manifest(regions_path).region_set
    cohorts = load_age_cohort_manifest(cohorts_path)
    validate_wpp_age5_mapping_compatibility(
        mapping_source_manifest=mapping_source_manifest,
        age5_manifest=raw_manifest,
        region_mapping=mapping,
    )
    cut = extract_macroregion_cohort_population(
        raw_path,
        year=year,
        dataset_id=raw_manifest.dataset_id,
        content_sha256=raw_manifest.content_sha256,
        region_mapping=mapping,
        region_set=regions,
        cohort_manifest=cohorts,
    )
    if cut.observation_class is not ObservationClass.OFFICIAL_ESTIMATE:
        raise ValueError("temporal validation cohort source must be an official estimate")
    if not cut.validation_eligible:
        raise ValueError("temporal validation cohort source must remain validation eligible")
    return render_cohort_population_csv(cut)


def _receipt_entry(payload: bytes) -> dict[str, int | str]:
    return {"sha256": _sha256(payload), "length_bytes": len(payload)}


def materialize(
    *,
    demographic_raw: Path,
    age5_raw: Path,
    demographic_manifest_path: Path,
    age5_manifest_path: Path,
    mapping_path: Path,
    regions_path: Path,
    cohorts_path: Path,
    canonical_2023_total_path: Path,
    canonical_2023_cohort_path: Path,
    output_dir: Path,
    transform_code_commit: str,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", transform_code_commit) is None:
        raise ValueError("transform_code_commit must be an exact lowercase Git SHA")

    demographic_manifest = load_dataset_manifest(demographic_manifest_path)
    age5_manifest = load_dataset_manifest(age5_manifest_path)
    _verify_raw_file(demographic_manifest, demographic_raw)
    _verify_raw_file(age5_manifest, age5_raw)

    total_2023 = _derive_total(
        raw_path=demographic_raw,
        raw_manifest=demographic_manifest,
        mapping_path=mapping_path,
        regions_path=regions_path,
        year=HOLDOUT_YEAR,
        transform_code_commit=transform_code_commit,
    )
    cohort_2023 = _derive_cohorts(
        raw_path=age5_raw,
        raw_manifest=age5_manifest,
        mapping_source_manifest=demographic_manifest,
        mapping_path=mapping_path,
        regions_path=regions_path,
        cohorts_path=cohorts_path,
        year=HOLDOUT_YEAR,
    )
    canonical_total_2023 = canonical_2023_total_path.read_bytes()
    canonical_cohort_2023 = canonical_2023_cohort_path.read_bytes()
    if total_2023 != canonical_total_2023:
        raise ValueError("2023 total-population control does not reproduce canonical bytes")
    if cohort_2023 != canonical_cohort_2023:
        raise ValueError("2023 cohort-population control does not reproduce canonical bytes")

    total_2022 = _derive_total(
        raw_path=demographic_raw,
        raw_manifest=demographic_manifest,
        mapping_path=mapping_path,
        regions_path=regions_path,
        year=INITIALIZATION_YEAR,
        transform_code_commit=transform_code_commit,
    )
    cohort_2022 = _derive_cohorts(
        raw_path=age5_raw,
        raw_manifest=age5_manifest,
        mapping_source_manifest=demographic_manifest,
        mapping_path=mapping_path,
        regions_path=regions_path,
        cohorts_path=cohorts_path,
        year=INITIALIZATION_YEAR,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    total_path = output_dir / "WZ_MACROREGION_V0_population_2022.csv"
    cohort_path = output_dir / "WZ_MACROREGION_V0_cohort_population_2022.csv"
    total_path.write_bytes(total_2022)
    cohort_path.write_bytes(cohort_2022)

    receipt: dict[str, Any] = {
        "schema_id": "WZ_DEMOGRAPHY_TEMPORAL_SPLIT_MATERIALIZATION_RECEIPT_V1",
        "transform_code_commit": transform_code_commit,
        "initialization_year": INITIALIZATION_YEAR,
        "holdout_year": HOLDOUT_YEAR,
        "sources": {
            demographic_manifest.dataset_id: {
                "sha256": demographic_manifest.content_sha256,
                "length_bytes": demographic_manifest.content_length_bytes,
            },
            age5_manifest.dataset_id: {
                "sha256": age5_manifest.content_sha256,
                "length_bytes": age5_manifest.content_length_bytes,
            },
        },
        "controls": {
            "canonical_2023_total": _receipt_entry(total_2023),
            "canonical_2023_cohort": _receipt_entry(cohort_2023),
        },
        "outputs": {
            total_path.name: _receipt_entry(total_2022),
            cohort_path.name: _receipt_entry(cohort_2022),
        },
    }
    receipt_path = output_dir / "WZ_DEMOGRAPHY_2022_2023_TEMPORAL_SPLIT_RECEIPT_V1.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demographic-raw", type=Path, required=True)
    parser.add_argument("--age5-raw", type=Path, required=True)
    parser.add_argument(
        "--demographic-manifest",
        type=Path,
        default=Path("data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml"),
    )
    parser.add_argument(
        "--age5-manifest",
        type=Path,
        default=Path("data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml"),
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml"),
    )
    parser.add_argument("--regions", type=Path, default=Path("regions/WZ_MACROREGION_V0.yaml"))
    parser.add_argument("--cohorts", type=Path, default=Path("data/cohorts/WZ_AGE_COHORT_V0.yaml"))
    parser.add_argument(
        "--canonical-2023-total",
        type=Path,
        default=Path("data/derived/wpp2024/WZ_MACROREGION_V0_population_2023.csv"),
    )
    parser.add_argument(
        "--canonical-2023-cohort",
        type=Path,
        default=Path("data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2023.csv"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--transform-code-commit", required=True)
    args = parser.parse_args()

    receipt = materialize(
        demographic_raw=args.demographic_raw,
        age5_raw=args.age5_raw,
        demographic_manifest_path=args.demographic_manifest,
        age5_manifest_path=args.age5_manifest,
        mapping_path=args.mapping,
        regions_path=args.regions,
        cohorts_path=args.cohorts,
        canonical_2023_total_path=args.canonical_2023_total,
        canonical_2023_cohort_path=args.canonical_2023_cohort,
        output_dir=args.output_dir,
        transform_code_commit=args.transform_code_commit,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
