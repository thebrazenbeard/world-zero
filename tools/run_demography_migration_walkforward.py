"""Run the frozen 2017->2018 migration walk-forward A/B experiment."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.manifests import DatasetAdmissionStatus, DatasetManifest, load_dataset_manifest
from worldzero.data.wpp2024 import WPP2024_FIELDS, WPP2024_VARIANT
from worldzero.data.wpp_age5 import (
    WPP2024_AGE5_FIELDS,
    WPP2024_AGE5_VARIANT,
    extract_macroregion_cohort_population,
    validate_wpp_age5_mapping_compatibility,
)
from worldzero.models.native_backbone import NativeBackboneConfig, run_native_backbone
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import load_region_mapping_manifest
from worldzero.sectors.demography import (
    AgeCohort,
    DemographyRates,
    MigrationLink,
    population_stock_id,
)
from worldzero.sectors.distribution import DistributionParams
from worldzero.sectors.production import ProductionParams
from worldzero.validation.demography_walkforward import (
    canonical_walkforward_report_bytes,
    compare_walkforward_scores,
    load_walkforward_contract,
    score_terminal_population,
)

CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_2017_TO_2018_V1.yaml"
)
MAPPING = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
COHORTS = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")
BOUNDARY_GROUP = {
    AgeCohort.CHILD: "10-14",
    AgeCohort.YOUNG_ADULT: "35-39",
    AgeCohort.MATURE_ADULT: "60-64",
}


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_raw(manifest: DatasetManifest, path: Path) -> None:
    if manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
        raise ValueError("raw source manifest must be ADMITTED")
    payload = path.read_bytes()
    if manifest.content_length_bytes is None:
        raise ValueError("raw source manifest must bind content length")
    if len(payload) != manifest.content_length_bytes:
        raise ValueError("raw source length mismatch")
    if hashlib.sha256(payload).hexdigest() != manifest.content_sha256:
        raise ValueError("raw source digest mismatch")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError("git provenance command failed: " + " ".join(args))
    return completed.stdout.strip()


def _source_identity(root: Path, expected_commit: str | None) -> tuple[str, str]:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("source worktree must be clean")
    commit = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if expected_commit is not None and commit != expected_commit:
        raise ValueError("source commit does not match expected commit")
    return commit, tree


def _mean(left: float, right: float) -> float:
    return (left + right) / 2.0


def _load_cohort_states(
    *,
    root: Path,
    age5_raw: Path,
    age5_manifest: DatasetManifest,
    years: tuple[int, ...],
) -> dict[int, dict[str, dict[AgeCohort, float]]]:
    mapping_source_manifest = load_dataset_manifest(
        root / "data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml"
    )
    mapping = load_region_mapping_manifest(root / MAPPING)
    regions = load_region_set_manifest(root / REGIONS).region_set
    cohort_manifest = load_age_cohort_manifest(root / COHORTS)
    validate_wpp_age5_mapping_compatibility(
        mapping_source_manifest=mapping_source_manifest,
        age5_manifest=age5_manifest,
        region_mapping=mapping,
    )
    result: dict[int, dict[str, dict[AgeCohort, float]]] = {}
    for year in years:
        cut = extract_macroregion_cohort_population(
            age5_raw,
            year=year,
            dataset_id=age5_manifest.dataset_id,
            content_sha256=age5_manifest.content_sha256,
            region_mapping=mapping,
            region_set=regions,
            cohort_manifest=cohort_manifest,
        )
        result[year] = {
            region_id: {cohort: float(value) for cohort, value in values.items()}
            for region_id, values in cut.values.items()
        }
    return result


def _load_boundary_populations(
    *,
    root: Path,
    age5_raw: Path,
    years: tuple[int, int],
) -> dict[int, dict[str, dict[AgeCohort, float]]]:
    mapping = load_region_mapping_manifest(root / MAPPING)
    regions = load_region_set_manifest(root / REGIONS).region_set
    source_to_region = mapping.source_to_target
    result: dict[int, dict[str, dict[AgeCohort, float]]] = {
        year: {
            region_id: {
                AgeCohort.CHILD: 0.0,
                AgeCohort.YOUNG_ADULT: 0.0,
                AgeCohort.MATURE_ADULT: 0.0,
            }
            for region_id in regions.ids
        }
        for year in years
    }
    group_to_cohort = {value: key for key, value in BOUNDARY_GROUP.items()}

    with gzip.open(age5_raw, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_AGE5_FIELDS:
            raise ValueError("WPP age5 CSV schema does not match frozen contract")
        for row in reader:
            if not row["ISO3_code"]:
                continue
            year = int(row["Time"])
            if year not in result:
                continue
            if row["Variant"] != WPP2024_AGE5_VARIANT:
                raise ValueError("unexpected WPP age5 variant")
            cohort = group_to_cohort.get(row["AgeGrp"])
            if cohort is None:
                continue
            parent_id = row["ParentID"]
            if parent_id not in source_to_region:
                raise ValueError(f"unmapped WPP parent group: {parent_id}")
            raw = row["PopTotal"]
            if not raw:
                raise ValueError("missing boundary-group population")
            value = float(raw) * 1000.0
            if not math.isfinite(value) or value < 0:
                raise ValueError("boundary-group population must be finite and nonnegative")
            result[year][source_to_region[parent_id]][cohort] += value
    return result


def _load_vital_flows(
    *,
    root: Path,
    demographic_raw: Path,
    years: tuple[int, int],
) -> dict[int, dict[str, dict[str, float]]]:
    mapping = load_region_mapping_manifest(root / MAPPING)
    regions = load_region_set_manifest(root / REGIONS).region_set
    source_to_region = mapping.source_to_target
    result: dict[int, dict[str, dict[str, float]]] = {
        year: {
            region_id: {
                "population": 0.0,
                "births": 0.0,
                "deaths": 0.0,
                "net_migration": 0.0,
            }
            for region_id in regions.ids
        }
        for year in years
    }

    with gzip.open(demographic_raw, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_FIELDS:
            raise ValueError("WPP demographic CSV schema does not match frozen contract")
        for row in reader:
            if not row["ISO3_code"]:
                continue
            year = int(row["Time"])
            if year not in result:
                continue
            if row["Variant"] != WPP2024_VARIANT:
                raise ValueError("unexpected WPP demographic variant")
            parent_id = row["ParentID"]
            if parent_id not in source_to_region:
                raise ValueError(f"unmapped WPP parent group: {parent_id}")
            if not row["TPopulation1July"] or not row["CBR"] or not row["CDR"] or not row["CNMR"]:
                raise ValueError("missing WPP population/CBR/CDR/CNMR fitting field")
            population_thousands = float(row["TPopulation1July"])
            cbr = float(row["CBR"])
            cdr = float(row["CDR"])
            cnmr = float(row["CNMR"])
            if population_thousands < 0 or cbr < 0 or cdr < 0:
                raise ValueError("WPP population/CBR/CDR fitting fields must be nonnegative")
            if not all(math.isfinite(value) for value in (population_thousands, cbr, cdr, cnmr)):
                raise ValueError("WPP fitting fields must be finite")
            region = source_to_region[parent_id]
            result[year][region]["population"] += population_thousands * 1000.0
            result[year][region]["births"] += population_thousands * cbr
            result[year][region]["deaths"] += population_thousands * cdr
            result[year][region]["net_migration"] += population_thousands * cnmr

    for year in years:
        for region_id, values in result[year].items():
            if values["population"] <= 0 or values["births"] <= 0 or values["deaths"] <= 0:
                raise ValueError(f"incomplete vital-flow coverage: {year}/{region_id}")
    return result


def _derive_demography_rates(
    *,
    regions: tuple[str, ...],
    broad: Mapping[int, Mapping[str, Mapping[AgeCohort, float]]],
    boundary: Mapping[int, Mapping[str, Mapping[AgeCohort, float]]],
    vital: Mapping[int, Mapping[str, Mapping[str, float]]],
    fit_years: tuple[int, int],
) -> dict[str, DemographyRates]:
    left, right = fit_years
    global_avg_stock = {
        cohort: sum(
            _mean(broad[left][region][cohort], broad[right][region][cohort])
            for region in regions
        )
        for cohort in AgeCohort
    }
    global_delta = {
        cohort: sum(
            broad[right][region][cohort] - broad[left][region][cohort]
            for region in regions
        )
        for cohort in AgeCohort
    }
    global_age_outflow = {
        cohort: sum(
            _mean(boundary[left][region][cohort], boundary[right][region][cohort])
            / 5.0
            for region in regions
        )
        for cohort in BOUNDARY_GROUP
    }
    global_births = sum(
        _mean(vital[left][region]["births"], vital[right][region]["births"])
        for region in regions
    )
    global_deaths = sum(
        _mean(vital[left][region]["deaths"], vital[right][region]["deaths"])
        for region in regions
    )

    mortality_shape = {
        AgeCohort.CHILD: (
            global_births
            - global_age_outflow[AgeCohort.CHILD]
            - global_delta[AgeCohort.CHILD]
        )
        / global_avg_stock[AgeCohort.CHILD],
        AgeCohort.YOUNG_ADULT: (
            global_age_outflow[AgeCohort.CHILD]
            - global_age_outflow[AgeCohort.YOUNG_ADULT]
            - global_delta[AgeCohort.YOUNG_ADULT]
        )
        / global_avg_stock[AgeCohort.YOUNG_ADULT],
        AgeCohort.MATURE_ADULT: (
            global_age_outflow[AgeCohort.YOUNG_ADULT]
            - global_age_outflow[AgeCohort.MATURE_ADULT]
            - global_delta[AgeCohort.MATURE_ADULT]
        )
        / global_avg_stock[AgeCohort.MATURE_ADULT],
        AgeCohort.OLDER_ADULT: (
            global_age_outflow[AgeCohort.MATURE_ADULT]
            - global_delta[AgeCohort.OLDER_ADULT]
        )
        / global_avg_stock[AgeCohort.OLDER_ADULT],
    }
    if any(not math.isfinite(value) or value < 0 for value in mortality_shape.values()):
        raise ValueError("global mortality shape must be finite and nonnegative")

    global_total = sum(global_avg_stock.values())
    observed_global_cdr = global_deaths / global_total
    if observed_global_cdr <= 0:
        raise ValueError("global crude death rate must be positive")

    rates: dict[str, DemographyRates] = {}
    for region in regions:
        avg_stock = {
            cohort: _mean(
                broad[left][region][cohort],
                broad[right][region][cohort],
            )
            for cohort in AgeCohort
        }
        avg_births = _mean(vital[left][region]["births"], vital[right][region]["births"])
        avg_deaths = _mean(vital[left][region]["deaths"], vital[right][region]["deaths"])
        total = sum(avg_stock.values())
        regional_cdr = avg_deaths / total
        scale = regional_cdr / observed_global_cdr

        ageing: dict[AgeCohort, float] = {}
        for cohort in BOUNDARY_GROUP:
            ageing[cohort] = (
                _mean(
                    boundary[left][region][cohort],
                    boundary[right][region][cohort],
                )
                / 5.0
                / avg_stock[cohort]
            )
        ageing[AgeCohort.OLDER_ADULT] = 0.0
        mortality = {
            cohort: mortality_shape[cohort] * scale for cohort in AgeCohort
        }
        values = [*ageing.values(), *mortality.values(), avg_births]
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("derived demography rates must be finite and nonnegative")
        rates[region] = DemographyRates(
            birth_rate_per_young_adult=avg_births / avg_stock[AgeCohort.YOUNG_ADULT],
            mortality=mortality,
            ageing=ageing,
        )
    return rates


def _balanced_migration_links(
    *,
    regions: tuple[str, ...],
    broad: Mapping[int, Mapping[str, Mapping[AgeCohort, float]]],
    vital: Mapping[int, Mapping[str, Mapping[str, float]]],
    fit_years: tuple[int, int],
) -> tuple[tuple[MigrationLink, ...], dict[str, Any]]:
    left, right = fit_years
    average_population = {
        region: sum(
            _mean(
                broad[left][region][cohort],
                broad[right][region][cohort],
            )
            for cohort in AgeCohort
        )
        for region in regions
    }
    average_net = {
        region: _mean(
            vital[left][region]["net_migration"],
            vital[right][region]["net_migration"],
        )
        for region in regions
    }
    donors = {region: -value for region, value in average_net.items() if value < 0}
    recipients = {region: value for region, value in average_net.items() if value > 0}
    total_out = sum(donors.values())
    total_in = sum(recipients.values())
    if total_out <= 0 or total_in <= 0:
        return (), {
            "average_net_migration_persons_per_year": average_net,
            "raw_total_outflow_persons_per_year": total_out,
            "raw_total_inflow_persons_per_year": total_in,
            "balanced_total_persons_per_year": 0.0,
            "links": [],
        }

    balanced_total = min(total_out, total_in)
    links: list[MigrationLink] = []
    rows: list[dict[str, float | str]] = []
    for donor in sorted(donors):
        donor_share = donors[donor] / total_out
        for recipient in sorted(recipients):
            recipient_share = recipients[recipient] / total_in
            flow = balanced_total * donor_share * recipient_share
            if flow <= 0:
                continue
            fraction = flow / average_population[donor]
            if not 0 < fraction <= 1:
                raise ValueError("derived migration fraction must be within (0, 1]")
            links.append(
                MigrationLink(
                    source_region=donor,
                    target_region=recipient,
                    annual_fraction=fraction,
                )
            )
            rows.append(
                {
                    "source_region": donor,
                    "target_region": recipient,
                    "flow_persons_per_year_at_fit_population": flow,
                    "annual_fraction": fraction,
                }
            )
    return tuple(links), {
        "average_net_migration_persons_per_year": average_net,
        "raw_total_outflow_persons_per_year": total_out,
        "raw_total_inflow_persons_per_year": total_in,
        "balanced_total_persons_per_year": balanced_total,
        "links": rows,
    }


def _parameter_digest(
    *,
    parameter_set_id: str,
    regions: tuple[str, ...],
    rates: Mapping[str, DemographyRates],
    links: tuple[MigrationLink, ...],
) -> str:
    payload = {
        "parameter_set_id": parameter_set_id,
        "rates": {
            region: {
                "birth_rate_per_young_adult": rates[region].birth_rate_per_young_adult,
                "mortality": {
                    cohort.value: rates[region].mortality[cohort]
                    for cohort in AgeCohort
                },
                "ageing": {
                    cohort.value: rates[region].ageing[cohort]
                    for cohort in AgeCohort
                },
            }
            for region in regions
        },
        "migration_links": [
            {
                "source_region": link.source_region,
                "target_region": link.target_region,
                "annual_fraction": link.annual_fraction,
            }
            for link in links
        ],
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _run_arm(
    *,
    regions,
    initial_population: Mapping[str, Mapping[AgeCohort, float]],
    rates: Mapping[str, DemographyRates],
    links: tuple[MigrationLink, ...],
    start: int,
    stop: int,
) -> dict[str, dict[str, float]]:
    production = {}
    distribution = {}
    for region in regions.ids:
        population = sum(initial_population[region].values())
        production[region] = ProductionParams(
            initial_productive_capital=population * 3.0,
            initial_service_capital=population,
            capital_output_ratio=3.0,
            labor_productivity=10.0,
            investment_share=0.0,
            service_investment_fraction=0.0,
            productive_depreciation_rate=0.0,
            service_depreciation_rate=0.0,
        )
        distribution[region] = DistributionParams(labor_share=0.65)

    result = run_native_backbone(
        NativeBackboneConfig(
            regions=regions,
            initial_population=initial_population,
            demography_rates=rates,
            migration_links=links,
            production=production,
            distribution=distribution,
            start=float(start),
            stop=float(stop),
            dt=0.25,
        )
    )
    terminal = result.states[-1]
    return {
        region: {
            cohort.value: terminal.value(population_stock_id(region, cohort))
            for cohort in AgeCohort
        }
        for region in regions.ids
    }


def execute_walkforward(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
    output_dir: Path,
    expected_source_commit: str | None,
) -> dict[str, Any]:
    contract = load_walkforward_contract(root / CONTRACT)
    source_commit, source_tree = _source_identity(root, expected_source_commit)

    age5_manifest = load_dataset_manifest(root / contract.source_age5_manifest)
    demographic_manifest = load_dataset_manifest(
        root / contract.source_demographic_manifest
    )
    _verify_raw(age5_manifest, age5_raw)
    _verify_raw(demographic_manifest, demographic_raw)

    fit_years = contract.fit_years
    regions = load_region_set_manifest(root / REGIONS).region_set
    broad = _load_cohort_states(
        root=root,
        age5_raw=age5_raw,
        age5_manifest=age5_manifest,
        years=fit_years,
    )
    boundary = _load_boundary_populations(
        root=root,
        age5_raw=age5_raw,
        years=fit_years,
    )
    vital = _load_vital_flows(
        root=root,
        demographic_raw=demographic_raw,
        years=fit_years,
    )
    rates = _derive_demography_rates(
        regions=regions.ids,
        broad=broad,
        boundary=boundary,
        vital=vital,
        fit_years=fit_years,
    )
    migration_links, migration_diagnostics = _balanced_migration_links(
        regions=regions.ids,
        broad=broad,
        vital=vital,
        fit_years=fit_years,
    )

    initial_population = broad[contract.initialization_year]
    baseline_terminal = _run_arm(
        regions=regions,
        initial_population=initial_population,
        rates=rates,
        links=(),
        start=contract.initialization_year,
        stop=contract.target_year,
    )
    candidate_terminal = _run_arm(
        regions=regions,
        initial_population=initial_population,
        rates=rates,
        links=migration_links,
        start=contract.initialization_year,
        stop=contract.target_year,
    )

    # Holdout extraction intentionally occurs only after both arms have executed.
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

    baseline_score = score_terminal_population(
        label="BASELINE_NO_MIGRATION",
        parameter_set_id=contract.baseline_parameter_set_id,
        terminal=baseline_terminal,
        observed=observed,
    )
    candidate_score = score_terminal_population(
        label="CANDIDATE_WITH_MIGRATION",
        parameter_set_id=contract.candidate_parameter_set_id,
        terminal=candidate_terminal,
        observed=observed,
    )
    comparison = compare_walkforward_scores(
        contract=contract,
        baseline=baseline_score,
        candidate=candidate_score,
    )

    baseline_parameter_sha = _parameter_digest(
        parameter_set_id=contract.baseline_parameter_set_id,
        regions=regions.ids,
        rates=rates,
        links=(),
    )
    candidate_parameter_sha = _parameter_digest(
        parameter_set_id=contract.candidate_parameter_set_id,
        regions=regions.ids,
        rates=rates,
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
        canonical_walkforward_report_bytes(comparison)
    )
    derivation = {
        "schema_id": "WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_DERIVATION_V1",
        "experiment_id": contract.experiment_id,
        "fit_years": list(fit_years),
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
        "baseline_parameter_sha256": baseline_parameter_sha,
        "candidate_parameter_sha256": candidate_parameter_sha,
        "migration": migration_diagnostics,
    }
    (output_dir / "derivation-receipt.json").write_bytes(
        _canonical_json_bytes(derivation)
    )
    receipt = {
        "schema_id": "WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_EXECUTION_V1",
        "experiment_id": contract.experiment_id,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "source_worktree_clean": True,
        "fit_years": list(fit_years),
        "initialization_year": contract.initialization_year,
        "target_year": contract.target_year,
        "baseline_parameter_sha256": baseline_parameter_sha,
        "candidate_parameter_sha256": candidate_parameter_sha,
        "migration_link_count": len(migration_links),
        "comparison_result": comparison.result,
        "baseline_result_sha256": baseline_score.result_sha256,
        "candidate_result_sha256": candidate_score.result_sha256,
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
        default=Path("runs/WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_2017_TO_2018_V1"),
    )
    args = parser.parse_args()
    result = execute_walkforward(
        root=args.root.resolve(),
        age5_raw=args.age5_raw.resolve(),
        demographic_raw=args.demographic_raw.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_MIGRATION_WALKFORWARD=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
