"""Deterministic execution output and runtime-only receipts for World Zero V0."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.models.bindings import (
    BaselineDataBundleManifest,
    BaselineParameterSet,
    build_world_zero_v0_config,
    load_baseline_data_bundle_manifest,
    load_baseline_parameter_set,
)
from worldzero.models.scenarios import ScenarioManifest, load_scenario_manifest
from worldzero.models.world_zero_v0 import WorldZeroV0Result, run_world_zero_v0


class FoodTradeSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    time: float
    local_consumption: dict[str, float]
    delivered_by_trade: dict[str, float]
    unmet_demand: dict[str, float]
    unused_supply: dict[str, float]
    total_losses: float
    trade_reconciliation_difference: float
    mass_balance_difference: float


class PolicySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    time: float
    requested_magnitude: float
    effective_magnitude: float
    active: bool


class BaselineResultDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_BASELINE_RESULT_V1"]
    scenario_id: str = Field(min_length=1)
    data_manifest_id: str = Field(min_length=1)
    parameter_set_id: str = Field(min_length=1)
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str = Field(min_length=1)
    times: tuple[float, ...]
    states: tuple[dict[str, float], ...]
    food_trade: tuple[FoodTradeSnapshot, ...]
    policy: tuple[PolicySnapshot, ...]


class ArtifactBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SizedArtifactBinding(ArtifactBinding):
    length_bytes: int = Field(ge=1)


class SourceLineageBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ResolvedDatasetBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["POPULATION_TOTAL", "POPULATION_COHORT"]
    dataset_id: str = Field(min_length=1)
    manifest: ArtifactBinding
    output: SizedArtifactBinding
    source_lineage: tuple[SourceLineageBinding, ...] = Field(min_length=1)
    transform_id: str = Field(min_length=1)
    transform_version: str = Field(min_length=1)
    transform_code_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str | None
    source_observation_class: str = Field(min_length=1)
    validation_eligible: bool


class SolverIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Literal["RK4Solver"]
    version: Literal["WORLD_ZERO_RK4_V0"]
    timestep: float = Field(gt=0)


class EnvironmentIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    python_implementation: str = Field(min_length=1)
    python_version: str = Field(min_length=1)
    operating_system: str = Field(min_length=1)


class RuntimeReceipt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_RUNTIME_RECEIPT_V1"]
    receipt_id: str = Field(min_length=1)
    claim_class: Literal["RUNNABLE_SOURCE_REPRODUCIBLE_ONLY"]
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_tree: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_worktree_clean: Literal[True]
    scenario: ArtifactBinding
    data_bundle: ArtifactBinding
    dataset_inputs: tuple[ResolvedDatasetBinding, ...] = Field(min_length=1)
    parameter_set: ArtifactBinding
    region_set: ArtifactBinding
    cohort_set: ArtifactBinding
    solver: SolverIdentity
    environment: EnvironmentIdentity
    result: ArtifactBinding


class _ResolvedSourceIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    tree: str = Field(pattern=r"^[0-9a-f]{40}$")


class _ResolvedRuntimeInputs(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scenario: ArtifactBinding
    data_bundle: ArtifactBinding
    parameter_set: ArtifactBinding
    region_set: ArtifactBinding
    cohort_set: ArtifactBinding


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _artifact_binding(root: Path, path: Path) -> ArtifactBinding:
    return ArtifactBinding(
        path=_display_path(root, path),
        sha256=_sha256(path),
    )


def _resolve_runtime_inputs(
    root: Path,
    *,
    scenario: Path,
    data_bundle: Path,
    parameter_set: Path,
    region_set: Path,
    cohort_set: Path,
) -> _ResolvedRuntimeInputs:
    return _ResolvedRuntimeInputs(
        scenario=_artifact_binding(root, scenario),
        data_bundle=_artifact_binding(root, data_bundle),
        parameter_set=_artifact_binding(root, parameter_set),
        region_set=_artifact_binding(root, region_set),
        cohort_set=_artifact_binding(root, cohort_set),
    )


def _snapshot_artifact(
    root: Path,
    source: Path,
    destination: Path,
) -> ArtifactBinding:
    payload = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return ArtifactBinding(
        path=_display_path(root, source),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _same_existing_file(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    try:
        return left.samefile(right)
    except OSError as exc:
        raise ValueError("runtime path identity could not be established") from exc


def _canonical_json_bytes(model: BaseModel) -> bytes:
    payload = model.model_dump(mode="json")
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _git(source_root: Path, *args: str) -> str:
    command = ["git", "-C", str(source_root), *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ValueError("git is unavailable; source provenance cannot be resolved") from exc
    if completed.returncode != 0:
        raise ValueError(f"git provenance command failed: {' '.join(args)}")
    return completed.stdout.strip()


def _resolve_source_identity(
    source_root: Path,
    *,
    expected_commit: str | None,
    expected_tree: str | None,
) -> _ResolvedSourceIdentity:
    requested_root = source_root.resolve()
    repository_root = Path(_git(requested_root, "rev-parse", "--show-toplevel")).resolve()
    executing_module = Path(__file__).resolve()
    source_package_root = repository_root / "src"
    if not executing_module.is_relative_to(source_package_root):
        raise ValueError("executing World Zero module is not inside the resolved Git checkout")

    worktree_status = _git(
        repository_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if worktree_status:
        raise ValueError("source worktree must be clean before runtime execution")

    commit = _git(repository_root, "rev-parse", "HEAD")
    tree = _git(repository_root, "rev-parse", "HEAD^{tree}")
    identity = _ResolvedSourceIdentity(commit=commit, tree=tree)
    if expected_commit is not None and identity.commit != expected_commit:
        raise ValueError("resolved source commit does not match expected commit")
    if expected_tree is not None and identity.tree != expected_tree:
        raise ValueError("resolved source tree does not match expected tree")
    return identity


def _resolve_dataset_inputs(
    root: Path,
    bundle: BaselineDataBundleManifest,
) -> tuple[ResolvedDatasetBinding, ...]:
    resolved: list[ResolvedDatasetBinding] = []
    for binding in bundle.bindings:
        manifest_path = _resolve(root, Path(binding.manifest_path))
        manifest = load_derived_dataset_manifest(manifest_path)
        if manifest.dataset_id != binding.dataset_id:
            raise ValueError(f"dataset binding identity mismatch: {binding.role}")

        output_path = _resolve(root, Path(manifest.output_path))
        output_bytes = output_path.read_bytes()
        output_sha256 = hashlib.sha256(output_bytes).hexdigest()
        if len(output_bytes) != manifest.output_length_bytes:
            raise ValueError(f"derived artifact length mismatch: {manifest.dataset_id}")
        if output_sha256 != manifest.output_sha256:
            raise ValueError(f"derived artifact digest mismatch: {manifest.dataset_id}")

        resolved.append(
            ResolvedDatasetBinding(
                role=binding.role,
                dataset_id=manifest.dataset_id,
                manifest=ArtifactBinding(
                    path=_display_path(root, manifest_path),
                    sha256=_sha256(manifest_path),
                ),
                output=SizedArtifactBinding(
                    path=_display_path(root, output_path),
                    sha256=output_sha256,
                    length_bytes=len(output_bytes),
                ),
                source_lineage=tuple(
                    SourceLineageBinding(
                        dataset_id=item.dataset_id,
                        content_sha256=item.content_sha256,
                    )
                    for item in manifest.source_lineage
                ),
                transform_id=manifest.transform_id,
                transform_version=manifest.transform_version,
                transform_code_commit=manifest.transform_code_commit,
                region_set_version=manifest.region_set_version,
                cohort_set_version=manifest.cohort_set_version,
                source_observation_class=manifest.source_observation_class.value,
                validation_eligible=manifest.validation_eligible,
            )
        )
    return tuple(resolved)


def _snapshot_dataset_inputs(
    root: Path,
    bundle: BaselineDataBundleManifest,
    snapshot_root: Path,
) -> tuple[tuple[ResolvedDatasetBinding, ...], Path, set[Path]]:
    resolved: list[ResolvedDatasetBinding] = []
    runtime_bindings = []
    protected_paths: set[Path] = set()

    for index, binding in enumerate(bundle.bindings):
        manifest_path = _resolve(root, Path(binding.manifest_path)).resolve()
        manifest_bytes = manifest_path.read_bytes()
        protected_paths.add(manifest_path)

        source_manifest_snapshot = snapshot_root / f"dataset-{index}-source-manifest.yaml"
        source_manifest_snapshot.write_bytes(manifest_bytes)
        manifest = load_derived_dataset_manifest(source_manifest_snapshot)
        if manifest.dataset_id != binding.dataset_id:
            raise ValueError(f"dataset binding identity mismatch: {binding.role}")

        output_path = _resolve(root, Path(manifest.output_path)).resolve()
        output_bytes = output_path.read_bytes()
        protected_paths.add(output_path)
        output_sha256 = hashlib.sha256(output_bytes).hexdigest()
        if len(output_bytes) != manifest.output_length_bytes:
            raise ValueError(f"derived artifact length mismatch: {manifest.dataset_id}")
        if output_sha256 != manifest.output_sha256:
            raise ValueError(f"derived artifact digest mismatch: {manifest.dataset_id}")

        runtime_output = snapshot_root / f"dataset-{index}-output"
        runtime_output.write_bytes(output_bytes)
        runtime_manifest = manifest.model_copy(update={"output_path": str(runtime_output)})
        runtime_manifest_path = snapshot_root / f"dataset-{index}-runtime-manifest.yaml"
        runtime_manifest_path.write_text(
            yaml.safe_dump(runtime_manifest.model_dump(mode="json"), sort_keys=False),
            encoding="utf-8",
        )
        runtime_bindings.append(
            binding.model_copy(update={"manifest_path": str(runtime_manifest_path)})
        )

        resolved.append(
            ResolvedDatasetBinding(
                role=binding.role,
                dataset_id=manifest.dataset_id,
                manifest=ArtifactBinding(
                    path=_display_path(root, manifest_path),
                    sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                ),
                output=SizedArtifactBinding(
                    path=_display_path(root, output_path),
                    sha256=output_sha256,
                    length_bytes=len(output_bytes),
                ),
                source_lineage=tuple(
                    SourceLineageBinding(
                        dataset_id=item.dataset_id,
                        content_sha256=item.content_sha256,
                    )
                    for item in manifest.source_lineage
                ),
                transform_id=manifest.transform_id,
                transform_version=manifest.transform_version,
                transform_code_commit=manifest.transform_code_commit,
                region_set_version=manifest.region_set_version,
                cohort_set_version=manifest.cohort_set_version,
                source_observation_class=manifest.source_observation_class.value,
                validation_eligible=manifest.validation_eligible,
            )
        )

    runtime_bundle = bundle.model_copy(update={"bindings": tuple(runtime_bindings)})
    runtime_bundle_path = snapshot_root / "data-bundle-runtime.yaml"
    runtime_bundle_path.write_text(
        yaml.safe_dump(runtime_bundle.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return tuple(resolved), runtime_bundle_path, protected_paths


def _run_from_verified_snapshot(
    *,
    root: Path,
    scenario_path: Path,
    data_bundle_path: Path,
    parameter_set_path: Path,
    region_set_path: Path,
    cohort_set_path: Path,
    output_path: Path,
    receipt_path: Path,
) -> tuple[
    ScenarioManifest,
    BaselineDataBundleManifest,
    BaselineParameterSet,
    _ResolvedRuntimeInputs,
    tuple[ResolvedDatasetBinding, ...],
    WorldZeroV0Result,
]:
    with tempfile.TemporaryDirectory(prefix="world-zero-runtime-") as temporary:
        snapshot_root = Path(temporary)
        scenario_snapshot = snapshot_root / "scenario.yaml"
        bundle_source_snapshot = snapshot_root / "data-bundle-source.yaml"
        parameters_snapshot = snapshot_root / "parameters.yaml"
        region_snapshot = snapshot_root / "region-set.yaml"
        cohort_snapshot = snapshot_root / "cohort-set.yaml"

        runtime_inputs = _ResolvedRuntimeInputs(
            scenario=_snapshot_artifact(root, scenario_path, scenario_snapshot),
            data_bundle=_snapshot_artifact(root, data_bundle_path, bundle_source_snapshot),
            parameter_set=_snapshot_artifact(root, parameter_set_path, parameters_snapshot),
            region_set=_snapshot_artifact(root, region_set_path, region_snapshot),
            cohort_set=_snapshot_artifact(root, cohort_set_path, cohort_snapshot),
        )
        scenario = load_scenario_manifest(scenario_snapshot)
        bundle = load_baseline_data_bundle_manifest(bundle_source_snapshot)
        parameters = load_baseline_parameter_set(parameters_snapshot)
        dataset_inputs, runtime_bundle_path, dataset_paths = _snapshot_dataset_inputs(
            root,
            bundle,
            snapshot_root,
        )

        protected_input_paths = {
            scenario_path.resolve(),
            data_bundle_path.resolve(),
            parameter_set_path.resolve(),
            region_set_path.resolve(),
            cohort_set_path.resolve(),
            *dataset_paths,
        }
        if output_path == receipt_path or _same_existing_file(output_path, receipt_path):
            raise ValueError("runtime output and receipt paths must differ")
        if (
            output_path in protected_input_paths
            or receipt_path in protected_input_paths
            or any(_same_existing_file(output_path, item) for item in protected_input_paths)
            or any(_same_existing_file(receipt_path, item) for item in protected_input_paths)
        ):
            raise ValueError("runtime output paths must not overwrite runtime inputs")

        config = build_world_zero_v0_config(
            root=snapshot_root,
            scenario_path=scenario_snapshot,
            data_bundle_path=runtime_bundle_path,
            parameter_set_path=parameters_snapshot,
            region_set_path=region_snapshot,
            cohort_set_path=cohort_snapshot,
        )
        result = run_world_zero_v0(config)
        return scenario, bundle, parameters, runtime_inputs, dataset_inputs, result


def execute_baseline_to_files(
    *,
    root: Path,
    scenario_path: Path,
    data_bundle_path: Path,
    parameter_set_path: Path,
    output_path: Path,
    receipt_path: Path,
    source_root: Path,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
    region_set_path: Path = Path("regions/WZ_MACROREGION_V0.yaml"),
    cohort_set_path: Path = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml"),
) -> RuntimeReceipt:
    source_identity = _resolve_source_identity(
        source_root,
        expected_commit=expected_source_commit,
        expected_tree=expected_source_tree,
    )
    resolved_scenario = _resolve(root, scenario_path)
    resolved_bundle = _resolve(root, data_bundle_path)
    resolved_parameters = _resolve(root, parameter_set_path)
    resolved_region_set = _resolve(root, region_set_path)
    resolved_cohort_set = _resolve(root, cohort_set_path)

    resolved_output = _resolve(root, output_path).resolve()
    resolved_receipt = _resolve(root, receipt_path).resolve()
    (
        scenario,
        bundle,
        parameters,
        runtime_inputs_before,
        dataset_inputs_before,
        result,
    ) = _run_from_verified_snapshot(
        root=root,
        scenario_path=resolved_scenario,
        data_bundle_path=resolved_bundle,
        parameter_set_path=resolved_parameters,
        region_set_path=resolved_region_set,
        cohort_set_path=resolved_cohort_set,
        output_path=resolved_output,
        receipt_path=resolved_receipt,
    )

    dataset_inputs_after = _resolve_dataset_inputs(root, bundle)
    if dataset_inputs_before != dataset_inputs_after:
        raise ValueError("resolved runtime data inputs changed during execution")
    runtime_inputs_after = _resolve_runtime_inputs(
        root,
        scenario=resolved_scenario,
        data_bundle=resolved_bundle,
        parameter_set=resolved_parameters,
        region_set=resolved_region_set,
        cohort_set=resolved_cohort_set,
    )
    if runtime_inputs_before != runtime_inputs_after:
        raise ValueError("resolved runtime control inputs changed during execution")
    source_identity_after = _resolve_source_identity(
        source_root,
        expected_commit=source_identity.commit,
        expected_tree=source_identity.tree,
    )
    if source_identity_after != source_identity:
        raise ValueError("resolved source identity changed during execution")

    states = tuple(
        {str(stock_id): value for stock_id, value in state.values.items()}
        for state in result.native.states
    )
    food_trade = tuple(
        FoodTradeSnapshot(
            time=time,
            local_consumption=dict(trade.local_consumption),
            delivered_by_trade=dict(trade.delivered_by_trade),
            unmet_demand=dict(trade.unmet_demand),
            unused_supply=dict(trade.unused_supply),
            total_losses=trade.total_losses,
            trade_reconciliation_difference=trade.trade_reconciliation_difference,
            mass_balance_difference=trade.mass_balance_difference,
        )
        for time, trade in zip(result.native.times, result.food_trade, strict=True)
    )
    policy = tuple(
        PolicySnapshot(
            time=item.time,
            requested_magnitude=item.requested_magnitude,
            effective_magnitude=item.effective_magnitude,
            active=item.active,
        )
        for item in result.policy
    )
    document = BaselineResultDocument(
        schema_version="WORLD_ZERO_BASELINE_RESULT_V1",
        scenario_id=scenario.scenario_id,
        data_manifest_id=bundle.data_manifest_id,
        parameter_set_id=parameters.parameter_set_id,
        region_set_version=bundle.region_set_version,
        cohort_set_version=bundle.cohort_set_version,
        times=result.native.times,
        states=states,
        food_trade=food_trade,
        policy=policy,
    )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = _canonical_json_bytes(document)
    resolved_output.write_bytes(output_bytes)
    result_sha256 = hashlib.sha256(output_bytes).hexdigest()

    receipt = RuntimeReceipt(
        schema_version="WORLD_ZERO_RUNTIME_RECEIPT_V1",
        receipt_id=f"{scenario.scenario_id}:{result_sha256[:16]}",
        claim_class="RUNNABLE_SOURCE_REPRODUCIBLE_ONLY",
        source_commit=source_identity.commit,
        source_tree=source_identity.tree,
        source_worktree_clean=True,
        scenario=runtime_inputs_before.scenario,
        data_bundle=runtime_inputs_before.data_bundle,
        dataset_inputs=dataset_inputs_before,
        parameter_set=runtime_inputs_before.parameter_set,
        region_set=runtime_inputs_before.region_set,
        cohort_set=runtime_inputs_before.cohort_set,
        solver=SolverIdentity(
            name="RK4Solver",
            version="WORLD_ZERO_RK4_V0",
            timestep=scenario.dt,
        ),
        environment=EnvironmentIdentity(
            python_implementation=sys.implementation.name,
            python_version=platform.python_version(),
            operating_system=platform.system(),
        ),
        result=ArtifactBinding(
            path=_display_path(root, resolved_output),
            sha256=result_sha256,
        ),
    )

    resolved_receipt.parent.mkdir(parents=True, exist_ok=True)
    resolved_receipt.write_bytes(_canonical_json_bytes(receipt))
    return receipt
