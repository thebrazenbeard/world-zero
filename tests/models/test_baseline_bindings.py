import csv
import hashlib
from pathlib import Path

import pytest
import yaml

from worldzero.models.bindings import (
    BaselineDataBundleManifest,
    build_world_zero_v0_config,
    load_baseline_data_bundle_manifest,
    load_baseline_parameter_set,
    resolve_baseline_population,
)
from worldzero.models.world_zero_v0 import run_world_zero_v0
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort

CANONICAL_BUNDLE = Path("data/bundles/WORLD_ZERO_2026_BASELINE_DATA_V0.yaml")
CANONICAL_PARAMETERS = Path(
    "scenarios/parameters/WORLD_ZERO_2026_PROVISIONAL_EXECUTION_V1.yaml"
)
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
COHORTS = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")


def _write_derived_manifest(
    path: Path,
    *,
    dataset_id: str,
    output_path: Path,
    output_sha256: str,
    output_length_bytes: int,
    cohort_set_version: str | None,
) -> None:
    payload = {
        "schema_id": "WORLD_ZERO_DERIVED_DATASET_MANIFEST_V1",
        "dataset_id": dataset_id,
        "source_lineage": [
            {
                "dataset_id": "synthetic-wpp-source",
                "content_sha256": "a" * 64,
            }
        ],
        "transform_id": "SYNTHETIC_TEST_TRANSFORM",
        "transform_version": "1.0.0",
        "transform_code_commit": "9d3d71bf98fb8924891b6b0163ca27f9c989b088",
        "region_set_version": "WZ_MACROREGION_V0",
        "cohort_set_version": cohort_set_version,
        "years": [2026],
        "unit": "persons",
        "observation_class": "DERIVED",
        "source_observation_class": "PROJECTION",
        "validation_eligible": False,
        "output_path": str(output_path),
        "output_sha256": output_sha256,
        "output_length_bytes": output_length_bytes,
        "generated_at": "2026-09-18T00:00:00Z",
        "admission_status": "ADMITTED",
        "admission_record_id": f"{dataset_id}-admission",
        "notes": "Synthetic runtime-binding test fixture.",
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_population_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    regions = load_region_set_manifest(REGIONS).region_set

    total_path = tmp_path / "population_total.csv"
    with total_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "region_id",
                "year",
                "population_persons",
                "source_observation_class",
                "observation_class",
                "validation_eligible",
            )
        )
        for region_id in regions.ids:
            writer.writerow((region_id, 2026, 4000, "PROJECTION", "DERIVED", "false"))

    cohort_path = tmp_path / "population_cohort.csv"
    with cohort_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "region_id",
                "year",
                "cohort_id",
                "population_persons",
                "source_observation_class",
                "observation_class",
                "validation_eligible",
            )
        )
        for region_id in regions.ids:
            for cohort in AgeCohort:
                writer.writerow(
                    (region_id, 2026, cohort.value, 1000, "PROJECTION", "DERIVED", "false")
                )

    total_manifest = tmp_path / "total_manifest.yaml"
    total_bytes = total_path.read_bytes()
    _write_derived_manifest(
        total_manifest,
        dataset_id="synthetic-total-2026",
        output_path=total_path,
        output_sha256=hashlib.sha256(total_bytes).hexdigest(),
        output_length_bytes=len(total_bytes),
        cohort_set_version=None,
    )

    cohort_manifest = tmp_path / "cohort_manifest.yaml"
    cohort_bytes = cohort_path.read_bytes()
    _write_derived_manifest(
        cohort_manifest,
        dataset_id="synthetic-cohort-2026",
        output_path=cohort_path,
        output_sha256=hashlib.sha256(cohort_bytes).hexdigest(),
        output_length_bytes=len(cohort_bytes),
        cohort_set_version="WZ_AGE_COHORT_V0",
    )
    return total_manifest, cohort_manifest


def _ready_bundle(
    total_manifest: Path,
    cohort_manifest: Path,
) -> BaselineDataBundleManifest:
    return BaselineDataBundleManifest.model_validate(
        {
            "schema_version": "WORLD_ZERO_DATA_BUNDLE_V1",
            "data_manifest_id": "SYNTHETIC_READY_DATA_BUNDLE",
            "status": "READY",
            "region_set_version": "WZ_MACROREGION_V0",
            "cohort_set_version": "WZ_AGE_COHORT_V0",
            "year": 2026,
            "population_reconciliation_tolerance_persons": 0,
            "bindings": [
                {
                    "role": "POPULATION_TOTAL",
                    "dataset_id": "synthetic-total-2026",
                    "manifest_path": str(total_manifest),
                },
                {
                    "role": "POPULATION_COHORT",
                    "dataset_id": "synthetic-cohort-2026",
                    "manifest_path": str(cohort_manifest),
                },
            ],
            "notes": "Synthetic READY bundle for runtime-binding tests.",
        }
    )


def test_canonical_data_bundle_remains_fail_closed_until_cohort_artifact_exists():
    bundle = load_baseline_data_bundle_manifest(CANONICAL_BUNDLE)
    assert bundle.status == "BINDING_REQUIRED"
    assert set(bundle.binding_by_role) == {"POPULATION_TOTAL"}


def test_provisional_parameter_set_is_explicitly_modeling_assumption_only():
    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    assert parameters.status == "PROVISIONAL_EXECUTION"
    assert parameters.evidence_class == "MODELING_ASSUMPTION"
    assert parameters.region_set_version == load_region_set_manifest(REGIONS).region_set.version
    assert parameters.region_overrides == {}


def test_ready_bundle_rejects_non_admitted_population_manifest(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    payload = yaml.safe_load(total_manifest.read_text(encoding="utf-8"))
    payload["admission_status"] = "QUALITY_CHECKED"
    payload["admission_record_id"] = None
    total_manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    bundle = _ready_bundle(total_manifest, cohort_manifest)
    regions = load_region_set_manifest(REGIONS).region_set
    with pytest.raises(ValueError, match="must be ADMITTED"):
        resolve_baseline_population(
            root=tmp_path,
            bundle=bundle,
            region_ids=regions.ids,
        )


def test_ready_bundle_rejects_non_person_population_units(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    payload = yaml.safe_load(cohort_manifest.read_text(encoding="utf-8"))
    payload["unit"] = "thousands of persons"
    cohort_manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    bundle = _ready_bundle(total_manifest, cohort_manifest)
    regions = load_region_set_manifest(REGIONS).region_set
    with pytest.raises(ValueError, match="unit must be persons"):
        resolve_baseline_population(
            root=tmp_path,
            bundle=bundle,
            region_ids=regions.ids,
        )


def test_ready_bundle_builds_and_runs_native_v0_end_to_end(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)

    bundle = _ready_bundle(total_manifest, cohort_manifest)
    data_manifest_id = bundle.data_manifest_id
    bundle_path = tmp_path / "bundle.yaml"
    bundle_path.write_text(
        yaml.safe_dump(bundle.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    scenario_path = tmp_path / "scenario.yaml"
    scenario_payload = {
        "schema_version": "WORLD_ZERO_SCENARIO_V1",
        "scenario_id": "SYNTHETIC_2026_RUNTIME",
        "scenario_class": "NATIVE_BASELINE",
        "status": "EXECUTABLE",
        "start": 2026.0,
        "stop": 2026.5,
        "dt": 0.25,
        "region_set_version": "WZ_MACROREGION_V0",
        "data_manifest_id": data_manifest_id,
        "parameter_set_id": parameters.parameter_set_id,
        "reference_artifact": None,
        "reference_sha256": None,
        "notes": "Synthetic executable runtime-binding test.",
    }
    scenario_path.write_text(
        yaml.safe_dump(scenario_payload, sort_keys=False),
        encoding="utf-8",
    )

    config = build_world_zero_v0_config(
        root=tmp_path,
        scenario_path=scenario_path,
        data_bundle_path=bundle_path,
        parameter_set_path=CANONICAL_PARAMETERS.resolve(),
        region_set_path=REGIONS.resolve(),
        cohort_set_path=COHORTS.resolve(),
    )
    result = run_world_zero_v0(config)

    assert result.native.global_population[0] == 40_000
    assert result.native.global_population[-1] == 40_000
    assert len(result.native.times) > 1
    assert len(result.food_trade) == len(result.native.times)
    assert all(abs(item.mass_balance_difference) <= 1e-9 for item in result.food_trade)
