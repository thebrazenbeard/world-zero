"""Deterministic execution output and runtime-only receipts for World Zero V0."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from worldzero.data.derived import load_derived_dataset_manifest
from worldzero.models.bindings import (
    BaselineDataBundleManifest,
    build_world_zero_v0_config,
    load_baseline_data_bundle_manifest,
    load_baseline_parameter_set,
)
from worldzero.models.scenarios import load_scenario_manifest
from worldzero.models.world_zero_v0 import run_world_zero_v0


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

    scenario = load_scenario_manifest(resolved_scenario)
    bundle = load_baseline_data_bundle_manifest(resolved_bundle)
    parameters = load_baseline_parameter_set(resolved_parameters)
    dataset_inputs_before = _resolve_dataset_inputs(root, bundle)

    config = build_world_zero_v0_config(
        root=root,
        scenario_path=resolved_scenario,
        data_bundle_path=resolved_bundle,
        parameter_set_path=resolved_parameters,
        region_set_path=resolved_region_set,
        cohort_set_path=resolved_cohort_set,
    )
    result = run_world_zero_v0(config)

    dataset_inputs_after = _resolve_dataset_inputs(root, bundle)
    if dataset_inputs_before != dataset_inputs_after:
        raise ValueError("resolved runtime data inputs changed during execution")

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

    resolved_output = _resolve(root, output_path)
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
        scenario=ArtifactBinding(
            path=_display_path(root, resolved_scenario),
            sha256=_sha256(resolved_scenario),
        ),
        data_bundle=ArtifactBinding(
            path=_display_path(root, resolved_bundle),
            sha256=_sha256(resolved_bundle),
        ),
        dataset_inputs=dataset_inputs_after,
        parameter_set=ArtifactBinding(
            path=_display_path(root, resolved_parameters),
            sha256=_sha256(resolved_parameters),
        ),
        region_set=ArtifactBinding(
            path=_display_path(root, resolved_region_set),
            sha256=_sha256(resolved_region_set),
        ),
        cohort_set=ArtifactBinding(
            path=_display_path(root, resolved_cohort_set),
            sha256=_sha256(resolved_cohort_set),
        ),
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

    resolved_receipt = _resolve(root, receipt_path)
    resolved_receipt.parent.mkdir(parents=True, exist_ok=True)
    resolved_receipt.write_bytes(_canonical_json_bytes(receipt))
    return receipt
