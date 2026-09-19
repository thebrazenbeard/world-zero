"""Run the frozen 2014->2015 regional older-adult mortality experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.run_demography_migration_walkforward import (
    _balanced_migration_links,
    _canonical_json_bytes,
    _derive_demography_rates,
    _load_boundary_populations,
    _load_cohort_states,
    _load_vital_flows,
    _parameter_digest,
    _run_arm,
    _source_identity,
    _verify_raw,
)
from worldzero.data.manifests import load_dataset_manifest
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort, DemographyRates, MigrationLink
from worldzero.validation.older_mortality_walkforward import (
    canonical_older_mortality_report_bytes,
    compare_older_mortality_scores,
    load_older_mortality_contract,
    score_older_mortality_terminal,
)

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_OLDER_MORTALITY_WALKFORWARD_2014_TO_2015_V1.yaml"
)
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")


def _net_cohort_migration(
    *,
    region_id: str,
    cohort: AgeCohort,
    links: tuple[MigrationLink, ...],
    average_stock: Mapping[str, Mapping[AgeCohort, float]],
) -> float:
    net = 0.0
    for link in links:
        flow = link.annual_fraction * average_stock[link.source_region][cohort]
        if link.source_region == region_id:
            net -= flow
        if link.target_region == region_id:
            net += flow
    return net


def _infer_regional_older_mortality(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
    age5_manifest,
    transitions: tuple[tuple[int, int], tuple[int, int]],
    broad: Mapping[int, Mapping[str, Mapping[AgeCohort, float]]],
) -> tuple[dict[str, float], dict[str, Any]]:
    regions = load_region_set_manifest(root / REGIONS).region_set
    rates_by_transition: dict[str, dict[str, float]] = {}
    diagnostics: dict[str, Any] = {}

    for left, right in transitions:
        boundary = _load_boundary_populations(
            root=root,
            age5_raw=age5_raw,
            years=(left, right),
        )
        vital = _load_vital_flows(
            root=root,
            demographic_raw=demographic_raw,
            years=(left, right),
        )
        links, migration = _balanced_migration_links(
            regions=regions.ids,
            broad=broad,
            vital=vital,
            fit_years=(left, right),
        )
        average_stock = {
            region: {
                cohort: (
                    broad[left][region][cohort] + broad[right][region][cohort]
                )
                / 2.0
                for cohort in AgeCohort
            }
            for region in regions.ids
        }

        transition_key = f"{left}_to_{right}"
        transition_rates: dict[str, float] = {}
        transition_diagnostics: dict[str, Any] = {}
        for region in regions.ids:
            older_average = average_stock[region][AgeCohort.OLDER_ADULT]
            if older_average <= 0:
                raise ValueError("older-adult average stock must be positive")
            mature_to_older = (
                (
                    boundary[left][region][AgeCohort.MATURE_ADULT]
                    + boundary[right][region][AgeCohort.MATURE_ADULT]
                )
                / 2.0
                / 5.0
            )
            net_older_migration = _net_cohort_migration(
                region_id=region,
                cohort=AgeCohort.OLDER_ADULT,
                links=links,
                average_stock=average_stock,
            )
            older_delta = (
                broad[right][region][AgeCohort.OLDER_ADULT]
                - broad[left][region][AgeCohort.OLDER_ADULT]
            )
            implied_deaths = mature_to_older + net_older_migration - older_delta
            rate = implied_deaths / older_average
            if not math.isfinite(rate) or rate < 0:
                raise ValueError(
                    f"negative/nonfinite older mortality residual: {transition_key}/{region}"
                )
            transition_rates[region] = rate
            transition_diagnostics[region] = {
                "older_average_persons": older_average,
                "mature_to_older_persons_per_year": mature_to_older,
                "net_older_migration_persons_per_year": net_older_migration,
                "older_stock_change_persons": older_delta,
                "implied_older_deaths_persons_per_year": implied_deaths,
                "implied_older_mortality_rate": rate,
            }

        rates_by_transition[transition_key] = transition_rates
        diagnostics[transition_key] = {
            "migration": migration,
            "regions": transition_diagnostics,
        }

    regional = {
        region: sum(
            rates_by_transition[f"{left}_to_{right}"][region]
            for left, right in transitions
        )
        / len(transitions)
        for region in regions.ids
    }
    return regional, {
        "transition_rates": rates_by_transition,
        "transition_diagnostics": diagnostics,
        "regional_smoothed_older_mortality": regional,
        "smoothing": "ARITHMETIC_MEAN_OF_TWO_TRANSITION_RATES",
        "negative_residual_policy": "FAIL_CLOSED",
        "source_age5_dataset_id": age5_manifest.dataset_id,
    }


def _candidate_rates(
    *,
    baseline: Mapping[str, DemographyRates],
    regional_older_mortality: Mapping[str, float],
) -> dict[str, DemographyRates]:
    candidate: dict[str, DemographyRates] = {}
    if set(baseline) != set(regional_older_mortality):
        raise ValueError("older-mortality regions do not match baseline rates")
    for region, rates in baseline.items():
        mortality = dict(rates.mortality)
        mortality[AgeCohort.OLDER_ADULT] = regional_older_mortality[region]
        candidate[region] = DemographyRates(
            birth_rate_per_young_adult=rates.birth_rate_per_young_adult,
            mortality=mortality,
            ageing=dict(rates.ageing),
        )
    return candidate


def execute_older_mortality_walkforward(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
    output_dir: Path,
    expected_source_commit: str | None,
) -> dict[str, Any]:
    contract = load_older_mortality_contract(root / CONTRACT)
    source_commit, source_tree = _source_identity(root, expected_source_commit)

    age5_manifest = load_dataset_manifest(root / contract.source_age5_manifest)
    demographic_manifest = load_dataset_manifest(
        root / contract.source_demographic_manifest
    )
    _verify_raw(age5_manifest, age5_raw)
    _verify_raw(demographic_manifest, demographic_raw)

    regions = load_region_set_manifest(root / REGIONS).region_set
    broad = _load_cohort_states(
        root=root,
        age5_raw=age5_raw,
        age5_manifest=age5_manifest,
        years=contract.history_years,
    )
    base_fit = contract.base_rate_fit_years
    base_boundary = _load_boundary_populations(
        root=root,
        age5_raw=age5_raw,
        years=base_fit,
    )
    base_vital = _load_vital_flows(
        root=root,
        demographic_raw=demographic_raw,
        years=base_fit,
    )
    baseline_rates = _derive_demography_rates(
        regions=regions.ids,
        broad=broad,
        boundary=base_boundary,
        vital=base_vital,
        fit_years=base_fit,
    )
    migration_links, migration_diagnostics = _balanced_migration_links(
        regions=regions.ids,
        broad=broad,
        vital=base_vital,
        fit_years=base_fit,
    )
    regional_older_mortality, older_diagnostics = _infer_regional_older_mortality(
        root=root,
        age5_raw=age5_raw,
        demographic_raw=demographic_raw,
        age5_manifest=age5_manifest,
        transitions=contract.older_mortality_transitions,
        broad=broad,
    )
    candidate_rates = _candidate_rates(
        baseline=baseline_rates,
        regional_older_mortality=regional_older_mortality,
    )

    initial_population = broad[contract.initialization_year]
    baseline_terminal = _run_arm(
        regions=regions,
        initial_population=initial_population,
        rates=baseline_rates,
        links=migration_links,
        start=contract.initialization_year,
        stop=contract.target_year,
    )
    candidate_terminal = _run_arm(
        regions=regions,
        initial_population=initial_population,
        rates=candidate_rates,
        links=migration_links,
        start=contract.initialization_year,
        stop=contract.target_year,
    )

    # Target extraction intentionally occurs only after both arms have executed.
    target = _load_cohort_states(
        root=root,
        age5_raw=age5_raw,
        age5_manifest=age5_manifest,
        years=(contract.target_year,),
    )[contract.target_year]
    observed = {
        region: {cohort.value: value for cohort, value in cohorts.items()}
        for region, cohorts in target.items()
    }

    baseline_score = score_older_mortality_terminal(
        label="BASELINE_GLOBAL_MORTALITY_SHAPE",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal=baseline_terminal,
        observed=observed,
    )
    candidate_score = score_older_mortality_terminal(
        label="CANDIDATE_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal=candidate_terminal,
        observed=observed,
    )
    comparison = compare_older_mortality_scores(
        contract=contract,
        baseline=baseline_score,
        candidate=candidate_score,
    )

    baseline_parameter_sha = _parameter_digest(
        parameter_set_id=contract.baseline_parameter_set_id,
        regions=regions.ids,
        rates=baseline_rates,
        links=migration_links,
    )
    candidate_parameter_sha = _parameter_digest(
        parameter_set_id=contract.candidate_parameter_set_id,
        regions=regions.ids,
        rates=candidate_rates,
        links=migration_links,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "baseline-terminal.json").write_bytes(
        _canonical_json_bytes(baseline_terminal)
    )
    (output_dir / "candidate-terminal.json").write_bytes(
        _canonical_json_bytes(candidate_terminal)
    )
    (output_dir / "comparison-report.json").write_bytes(
        canonical_older_mortality_report_bytes(comparison)
    )

    derivation = {
        "schema_id": "WZ_DEMOGRAPHY_OLDER_MORTALITY_DERIVATION_V1",
        "experiment_id": contract.experiment_id,
        "history_years": list(contract.history_years),
        "base_rate_fit_years": list(base_fit),
        "older_mortality_transitions": [
            list(item) for item in contract.older_mortality_transitions
        ],
        "initialization_year": contract.initialization_year,
        "target_year": contract.target_year,
        "holdout_extracted_after_execution": True,
        "source_inputs": {
            age5_manifest.dataset_id: {
                "sha256": age5_manifest.content_sha256,
                "length_bytes": age5_manifest.content_length_bytes,
            },
            demographic_manifest.dataset_id: {
                "sha256": demographic_manifest.content_sha256,
                "length_bytes": demographic_manifest.content_length_bytes,
            },
        },
        "run_migration": migration_diagnostics,
        "older_mortality": older_diagnostics,
        "baseline_parameter_sha256": baseline_parameter_sha,
        "candidate_parameter_sha256": candidate_parameter_sha,
    }
    (output_dir / "derivation-receipt.json").write_bytes(
        _canonical_json_bytes(derivation)
    )
    receipt = {
        "schema_id": "WZ_DEMOGRAPHY_OLDER_MORTALITY_EXECUTION_V1",
        "experiment_id": contract.experiment_id,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "source_worktree_clean": True,
        "history_years": list(contract.history_years),
        "initialization_year": contract.initialization_year,
        "target_year": contract.target_year,
        "migration_link_count": len(migration_links),
        "baseline_parameter_sha256": baseline_parameter_sha,
        "candidate_parameter_sha256": candidate_parameter_sha,
        "baseline_result_sha256": baseline_score.result_sha256,
        "candidate_result_sha256": candidate_score.result_sha256,
        "comparison_result": comparison.result,
        "claim_class": contract.result_claim,
    }
    (output_dir / "execution-receipt.json").write_bytes(
        _canonical_json_bytes(receipt)
    )
    return {
        "execution_receipt": receipt,
        "comparison": comparison.model_dump(mode="json"),
        "derivation": derivation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--age5-raw", type=Path, required=True)
    parser.add_argument("--demographic-raw", type=Path, required=True)
    parser.add_argument("--expected-source-commit")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/WZ_DEMOGRAPHY_OLDER_MORTALITY_WALKFORWARD_2014_TO_2015_V1"),
    )
    args = parser.parse_args()

    result = execute_older_mortality_walkforward(
        root=args.root.resolve(),
        age5_raw=args.age5_raw.resolve(),
        demographic_raw=args.demographic_raw.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_OLDER_MORTALITY_WALKFORWARD=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
