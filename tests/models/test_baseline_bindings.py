import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

import worldzero.models.execution as execution_module
from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.models.bindings import (
    BaselineDataBundleManifest,
    build_world_zero_v0_config,
    load_baseline_data_bundle_manifest,
    load_baseline_parameter_set,
    resolve_baseline_population,
)
from worldzero.models.execution import execute_baseline_to_files
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


def _write_ready_bundle(
    tmp_path: Path,
    *,
    total_manifest: Path,
    cohort_manifest: Path,
    tolerance_persons: float = 0,
) -> tuple[str, Path]:
    data_manifest_id = "SYNTHETIC_READY_DATA_BUNDLE"
    bundle_payload = {
        "schema_version": "WORLD_ZERO_DATA_BUNDLE_V1",
        "data_manifest_id": data_manifest_id,
        "status": "READY",
        "region_set_version": "WZ_MACROREGION_V0",
        "cohort_set_version": "WZ_AGE_COHORT_V0",
        "year": 2026,
        "population_reconciliation_tolerance_persons": tolerance_persons,
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
        "notes": "Synthetic READY bundle for end-to-end runtime test.",
    }
    bundle = BaselineDataBundleManifest.model_validate(bundle_payload)
    bundle_path = tmp_path / "bundle.yaml"
    bundle_path.write_text(
        yaml.safe_dump(bundle.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return data_manifest_id, bundle_path


def _write_synthetic_scenario(
    tmp_path: Path,
    *,
    data_manifest_id: str,
    parameter_set_id: str,
) -> Path:
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
        "parameter_set_id": parameter_set_id,
        "reference_artifact": None,
        "reference_sha256": None,
        "notes": "Synthetic executable runtime-binding test.",
    }
    scenario_path.write_text(
        yaml.safe_dump(scenario_payload, sort_keys=False),
        encoding="utf-8",
    )
    return scenario_path


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


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


def test_ready_bundle_rejects_unbounded_reconciliation_tolerance(tmp_path: Path):
    with pytest.raises(ValueError, match="tolerance exceeds V0 ceiling"):
        _write_ready_bundle(
            tmp_path,
            total_manifest=Path("total.yaml"),
            cohort_manifest=Path("cohort.yaml"),
            tolerance_persons=101,
        )


def test_ready_bundle_rejects_non_admitted_population_manifest(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    payload = yaml.safe_load(total_manifest.read_text(encoding="utf-8"))
    payload["admission_status"] = "QUALITY_CHECKED"
    payload["admission_record_id"] = None
    total_manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    _, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    bundle = load_baseline_data_bundle_manifest(bundle_path)
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
    _, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    bundle = load_baseline_data_bundle_manifest(bundle_path)
    regions = load_region_set_manifest(REGIONS).region_set
    with pytest.raises(ValueError, match="unit must be persons"):
        resolve_baseline_population(
            root=tmp_path,
            bundle=bundle,
            region_ids=regions.ids,
        )


def test_ready_bundle_rejects_hash_consistent_nonfinite_population(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    cohort_payload = yaml.safe_load(cohort_manifest.read_text(encoding="utf-8"))
    cohort_path = Path(cohort_payload["output_path"])

    with cohort_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = tuple(reader.fieldnames or ())
    rows[0]["population_persons"] = "nan"
    with cohort_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    cohort_bytes = cohort_path.read_bytes()
    cohort_payload["output_sha256"] = hashlib.sha256(cohort_bytes).hexdigest()
    cohort_payload["output_length_bytes"] = len(cohort_bytes)
    cohort_manifest.write_text(
        yaml.safe_dump(cohort_payload, sort_keys=False),
        encoding="utf-8",
    )

    _, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    bundle = load_baseline_data_bundle_manifest(bundle_path)
    regions = load_region_set_manifest(REGIONS).region_set
    with pytest.raises(ValueError, match="cohort population must be finite"):
        resolve_baseline_population(
            root=tmp_path,
            bundle=bundle,
            region_ids=regions.ids,
        )


def test_runtime_binding_models_reject_nonfinite_numbers(tmp_path: Path):
    with pytest.raises(ValueError):
        _write_ready_bundle(
            tmp_path,
            total_manifest=Path("total.yaml"),
            cohort_manifest=Path("cohort.yaml"),
            tolerance_persons=float("nan"),
        )


def test_runtime_receipt_rejects_control_change_during_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    data_manifest_id, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    scenario_path = _write_synthetic_scenario(
        tmp_path,
        data_manifest_id=data_manifest_id,
        parameter_set_id=parameters.parameter_set_id,
    )

    real_run = execution_module.run_world_zero_v0

    def mutating_run(config):
        result = real_run(config)
        payload = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
        payload["notes"] = "mutated during execution"
        scenario_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(execution_module, "run_world_zero_v0", mutating_run)
    with pytest.raises(ValueError, match="control inputs changed during execution"):
        execute_baseline_to_files(
            root=tmp_path,
            scenario_path=scenario_path,
            data_bundle_path=bundle_path,
            parameter_set_path=CANONICAL_PARAMETERS.resolve(),
            output_path=tmp_path / "runs" / "result.json",
            receipt_path=tmp_path / "runs" / "receipt.json",
            source_root=Path.cwd(),
            region_set_path=REGIONS.resolve(),
            cohort_set_path=COHORTS.resolve(),
        )


def test_runtime_receipt_refuses_output_aliasing_an_input(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    data_manifest_id, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    scenario_path = _write_synthetic_scenario(
        tmp_path,
        data_manifest_id=data_manifest_id,
        parameter_set_id=parameters.parameter_set_id,
    )

    with pytest.raises(ValueError, match="must not overwrite runtime inputs"):
        execute_baseline_to_files(
            root=tmp_path,
            scenario_path=scenario_path,
            data_bundle_path=bundle_path,
            parameter_set_path=CANONICAL_PARAMETERS.resolve(),
            output_path=scenario_path,
            receipt_path=tmp_path / "runs" / "receipt.json",
            source_root=Path.cwd(),
            region_set_path=REGIONS.resolve(),
            cohort_set_path=COHORTS.resolve(),
        )


def test_runtime_receipt_refuses_hardlink_aliasing_an_input(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    data_manifest_id, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )
    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    scenario_path = _write_synthetic_scenario(
        tmp_path,
        data_manifest_id=data_manifest_id,
        parameter_set_id=parameters.parameter_set_id,
    )

    output_path = tmp_path / "hardlinked-result.json"
    os.link(scenario_path, output_path)

    with pytest.raises(ValueError, match="must not overwrite runtime inputs"):
        execute_baseline_to_files(
            root=tmp_path,
            scenario_path=scenario_path,
            data_bundle_path=bundle_path,
            parameter_set_path=CANONICAL_PARAMETERS.resolve(),
            output_path=output_path,
            receipt_path=tmp_path / "runs" / "receipt.json",
            source_root=Path.cwd(),
            region_set_path=REGIONS.resolve(),
            cohort_set_path=COHORTS.resolve(),
        )


def test_ready_bundle_builds_and_runs_native_v0_end_to_end(tmp_path: Path):
    total_manifest, cohort_manifest = _write_population_artifacts(tmp_path)
    data_manifest_id, bundle_path = _write_ready_bundle(
        tmp_path,
        total_manifest=total_manifest,
        cohort_manifest=cohort_manifest,
    )

    parameters = load_baseline_parameter_set(CANONICAL_PARAMETERS)
    scenario_path = _write_synthetic_scenario(
        tmp_path,
        data_manifest_id=data_manifest_id,
        parameter_set_id=parameters.parameter_set_id,
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

    output_path = tmp_path / "runs" / "result.json"
    receipt_path = tmp_path / "runs" / "receipt.json"
    with pytest.raises(ValueError, match="expected commit"):
        execute_baseline_to_files(
            root=tmp_path,
            scenario_path=scenario_path,
            data_bundle_path=bundle_path,
            parameter_set_path=CANONICAL_PARAMETERS.resolve(),
            output_path=output_path,
            receipt_path=receipt_path,
            source_root=Path.cwd(),
            expected_source_commit="0" * 40,
            region_set_path=REGIONS.resolve(),
            cohort_set_path=COHORTS.resolve(),
        )

    receipt = execute_baseline_to_files(
        root=tmp_path,
        scenario_path=scenario_path,
        data_bundle_path=bundle_path,
        parameter_set_path=CANONICAL_PARAMETERS.resolve(),
        output_path=output_path,
        receipt_path=receipt_path,
        source_root=Path.cwd(),
        region_set_path=REGIONS.resolve(),
        cohort_set_path=COHORTS.resolve(),
    )
    assert receipt.claim_class == "RUNNABLE_SOURCE_REPRODUCIBLE_ONLY"
    assert receipt.source_commit == _git("rev-parse", "HEAD")
    assert receipt.source_tree == _git("rev-parse", "HEAD^{tree}")
    assert receipt.source_worktree_clean is True
    assert receipt.result.sha256 == hashlib.sha256(output_path.read_bytes()).hexdigest()

    by_role = {item.role: item for item in receipt.dataset_inputs}
    assert set(by_role) == {"POPULATION_TOTAL", "POPULATION_COHORT"}
    total_source = load_derived_dataset_manifest(total_manifest)
    cohort_source = load_derived_dataset_manifest(cohort_manifest)
    assert by_role["POPULATION_TOTAL"].manifest.sha256 == hashlib.sha256(
        total_manifest.read_bytes()
    ).hexdigest()
    assert by_role["POPULATION_TOTAL"].output.sha256 == total_source.output_sha256
    assert by_role["POPULATION_TOTAL"].output.length_bytes == total_source.output_length_bytes
    assert by_role["POPULATION_COHORT"].manifest.sha256 == hashlib.sha256(
        cohort_manifest.read_bytes()
    ).hexdigest()
    assert by_role["POPULATION_COHORT"].output.sha256 == cohort_source.output_sha256
    assert by_role["POPULATION_COHORT"].output.length_bytes == cohort_source.output_length_bytes

    result_document = json.loads(output_path.read_text(encoding="utf-8"))
    assert result_document["schema_version"] == "WORLD_ZERO_BASELINE_RESULT_V1"
    assert result_document["scenario_id"] == "SYNTHETIC_2026_RUNTIME"
    receipt_document = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt_document["schema_version"] == "WORLD_ZERO_RUNTIME_RECEIPT_V1"
    assert receipt_document["source_commit"] == _git("rev-parse", "HEAD")
    assert len(receipt_document["dataset_inputs"]) == 2
