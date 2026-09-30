"""Run frozen 2018->2019 older-mortality mass-normalization experiment."""

from __future__ import annotations

import argparse
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
from tools.run_demography_older_mortality_walkforward import (
    _candidate_rates,
    _infer_regional_older_mortality,
)
from worldzero.data.manifests import load_dataset_manifest
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort, DemographyRates
from worldzero.validation.older_mortality_mass_normalization import (
    canonical_mass_normalization_report_bytes,
    compare_mass_normalization_scores,
    load_mass_normalization_contract,
    score_mass_normalization_terminal,
)

CONTRACT = Path(
    "science/scoring/"
    "WZ_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_2018_TO_2019_V1.yaml"
)
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")


def _normalize_regional_older_mortality(
    *,
    global_shape_rates: Mapping[str, DemographyRates],
    regional_older_mortality: Mapping[str, float],
    initial_population: Mapping[str, Mapping[AgeCohort, float]],
) -> tuple[dict[str, float], dict[str, float]]:
    if set(global_shape_rates) != set(regional_older_mortality):
        raise ValueError("regional mortality coverage mismatch")
    if set(global_shape_rates) != set(initial_population):
        raise ValueError("initial-population coverage mismatch")

    reference_mass = sum(
        global_shape_rates[region].mortality[AgeCohort.OLDER_ADULT]
        * initial_population[region][AgeCohort.OLDER_ADULT]
        for region in global_shape_rates
    )
    unnormalized_mass = sum(
        regional_older_mortality[region]
        * initial_population[region][AgeCohort.OLDER_ADULT]
        for region in global_shape_rates
    )
    if (
        not math.isfinite(reference_mass)
        or not math.isfinite(unnormalized_mass)
        or reference_mass <= 0
        or unnormalized_mass <= 0
    ):
        raise ValueError("older-adult death-mass normalization must be finite and positive")

    factor = reference_mass / unnormalized_mass
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("older-adult death-mass scale must be finite and positive")
    normalized = {
        region: regional_older_mortality[region] * factor
        for region in global_shape_rates
    }
    normalized_mass = sum(
        normalized[region] * initial_population[region][AgeCohort.OLDER_ADULT]
        for region in global_shape_rates
    )
    if not math.isclose(
        normalized_mass,
        reference_mass,
        rel_tol=1e-12,
        abs_tol=1e-6,
    ):
        raise ValueError("normalized older-adult death mass does not match reference")

    return normalized, {
        "reference_global_shape_death_mass_persons_per_year": reference_mass,
        "unnormalized_regional_death_mass_persons_per_year": unnormalized_mass,
        "normalization_factor": factor,
        "normalized_regional_death_mass_persons_per_year": normalized_mass,
    }


def execute_mass_normalization_walkforward(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
    output_dir: Path,
    expected_source_commit: str | None,
) -> dict[str, Any]:
    contract = load_mass_normalization_contract(root / CONTRACT)
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
    global_shape_rates = _derive_demography_rates(
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
    initial_population = broad[contract.initialization_year]
    normalized_older_mortality, normalization = _normalize_regional_older_mortality(
        global_shape_rates=global_shape_rates,
        regional_older_mortality=regional_older_mortality,
        initial_population=initial_population,
    )

    baseline_rates = _candidate_rates(
        baseline=global_shape_rates,
        regional_older_mortality=regional_older_mortality,
    )
    candidate_rates = _candidate_rates(
        baseline=global_shape_rates,
        regional_older_mortality=normalized_older_mortality,
    )

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

    baseline_score = score_mass_normalization_terminal(
        label="BASELINE_UNNORMALIZED_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal=baseline_terminal,
        observed=observed,
    )
    candidate_score = score_mass_normalization_terminal(
        label="CANDIDATE_MASS_NORMALIZED_REGIONAL_OLDER_MORTALITY",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal=candidate_terminal,
        observed=observed,
    )
    comparison = compare_mass_normalization_scores(
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
        canonical_mass_normalization_report_bytes(comparison)
    )

    derivation = {
        "schema_id": "WZ_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_DERIVATION_V1",
        "experiment_id": contract.experiment_id,
        "history_years": list(contract.history_years),
        "base_rate_fit_years": list(base_fit),
        "older_mortality_transitions": [
            list(item) for item in contract.older_mortality_transitions
        ],
        "initialization_year": contract.initialization_year,
        "target_year": contract.target_year,
        "holdout_extracted_after_execution": True,
        "target_used_for_normalization": False,
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
        "migration": migration_diagnostics,
        "older_mortality": older_diagnostics,
        "normalization": normalization,
        "normalized_regional_older_mortality": normalized_older_mortality,
        "baseline_parameter_sha256": baseline_parameter_sha,
        "candidate_parameter_sha256": candidate_parameter_sha,
    }
    (output_dir / "derivation-receipt.json").write_bytes(
        _canonical_json_bytes(derivation)
    )
    receipt = {
        "schema_id": "WZ_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_EXECUTION_V1",
        "experiment_id": contract.experiment_id,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "source_worktree_clean": True,
        "history_years": list(contract.history_years),
        "initialization_year": contract.initialization_year,
        "target_year": contract.target_year,
        "migration_link_count": len(migration_links),
        "normalization_factor": normalization["normalization_factor"],
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
        default=Path(
            "runs/WZ_DEMOGRAPHY_OLDER_MORTALITY_MASS_NORMALIZATION_2018_TO_2019_V1"
        ),
    )
    args = parser.parse_args()

    result = execute_mass_normalization_walkforward(
        root=args.root.resolve(),
        age5_raw=args.age5_raw.resolve(),
        demographic_raw=args.demographic_raw.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_OLDER_MORTALITY_MASS_NORMALIZATION=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
