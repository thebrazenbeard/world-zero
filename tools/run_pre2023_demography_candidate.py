"""Fit pre-2023 demography dynamics, execute 2022->2023, and compare once."""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.manifests import load_dataset_manifest
from worldzero.data.wpp2024 import WPP2024_FIELDS, WPP2024_VARIANT
from worldzero.data.wpp_age5 import (
    WPP2024_AGE5_FIELDS,
    WPP2024_AGE5_VARIANT,
    extract_macroregion_cohort_population,
)
from worldzero.models.execution import RuntimeReceipt, execute_baseline_to_files
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.regions.mapping import load_region_mapping_manifest
from worldzero.sectors.demography import AgeCohort
from worldzero.validation.temporal_population import (
    TemporalPopulationScoreReport,
    canonical_score_report_bytes,
    score_temporal_population_result,
)
from worldzero.validation.temporal_population_comparison import (
    TemporalPopulationComparisonReport,
    canonical_comparison_report_bytes,
    compare_temporal_population_scores,
    load_temporal_population_comparison_contract,
)

SCENARIO = Path("scenarios/2022_to_2023_pre2023_dynamics_v1.yaml")
DATA_BUNDLE = Path("data/bundles/WORLD_ZERO_2022_TEMPORAL_VALIDATION_DATA_V1.yaml")
BASE_PARAMETERS = Path(
    "scenarios/parameters/WORLD_ZERO_2022_TEMPORAL_SCORE_PROVISIONAL_V1.yaml"
)
SCORE_CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_2022_TO_2023_PRE2023_DYNAMICS_SCORE_CONTRACT_V1.yaml"
)
COMPARISON_CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_SUCCESSOR_VS_PERSISTENCE_COMPARISON_V1.yaml"
)
AGE5_MANIFEST = Path(
    "data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml"
)
DEMOGRAPHIC_MANIFEST = Path(
    "data/manifests/UN_WPP_2024_DEMOGRAPHIC_INDICATORS_MEDIUM_V1.yaml"
)
MAPPING = Path("regions/mappings/WPP2024_PARENT_TO_WZ_MACROREGION_V0.yaml")
REGIONS = Path("regions/WZ_MACROREGION_V0.yaml")
COHORTS = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml")
FIT_YEARS = (2021, 2022)
PARAMETER_SET_ID = "WORLD_ZERO_2022_PRE2023_DYNAMICS_V1"
BOUNDARY_GROUP = {
    AgeCohort.CHILD: "10-14",
    AgeCohort.YOUNG_ADULT: "35-39",
    AgeCohort.MATURE_ADULT: "60-64",
}


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_rate(value: float, *, label: str) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must resolve to a finite nonnegative rate")
    return value


def _mean(left: float, right: float) -> float:
    return (left + right) / 2.0


def _load_pre2023_cohort_state(
    *,
    root: Path,
    age5_raw: Path,
) -> tuple[
    dict[int, dict[str, dict[AgeCohort, float]]],
    dict[int, dict[str, dict[AgeCohort, float]]],
]:
    age5_manifest = load_dataset_manifest(root / AGE5_MANIFEST)
    mapping = load_region_mapping_manifest(root / MAPPING)
    regions = load_region_set_manifest(root / REGIONS).region_set
    cohort_manifest = load_age_cohort_manifest(root / COHORTS)

    broad: dict[int, dict[str, dict[AgeCohort, float]]] = {}
    for year in FIT_YEARS:
        cut = extract_macroregion_cohort_population(
            age5_raw,
            year=year,
            dataset_id=age5_manifest.dataset_id,
            content_sha256=age5_manifest.content_sha256,
            region_mapping=mapping,
            region_set=regions,
            cohort_manifest=cohort_manifest,
        )
        broad[year] = {
            region_id: {cohort: float(value) for cohort, value in values.items()}
            for region_id, values in cut.values.items()
        }

    boundary: dict[int, dict[str, dict[AgeCohort, float]]] = {
        year: {
            region_id: {
                AgeCohort.CHILD: 0.0,
                AgeCohort.YOUNG_ADULT: 0.0,
                AgeCohort.MATURE_ADULT: 0.0,
            }
            for region_id in regions.ids
        }
        for year in FIT_YEARS
    }
    source_to_region = mapping.source_to_target
    with gzip.open(age5_raw, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_AGE5_FIELDS:
            raise ValueError("WPP age5 CSV schema does not match frozen contract")
        for row in reader:
            if not row["ISO3_code"]:
                continue
            year = int(row["Time"])
            if year not in FIT_YEARS:
                continue
            if row["Variant"] != WPP2024_AGE5_VARIANT:
                raise ValueError("unexpected WPP age5 variant")
            parent_id = row["ParentID"]
            if parent_id not in source_to_region:
                raise ValueError(f"unmapped WPP parent group: {parent_id}")
            age_group = row["AgeGrp"]
            cohort = next(
                (
                    item
                    for item, boundary_group in BOUNDARY_GROUP.items()
                    if boundary_group == age_group
                ),
                None,
            )
            if cohort is None:
                continue
            raw_value = row["PopTotal"]
            if not raw_value:
                raise ValueError("missing boundary age-group population")
            value = float(raw_value) * 1000.0
            if value < 0:
                raise ValueError("boundary age-group population must be nonnegative")
            boundary[year][source_to_region[parent_id]][cohort] += value

    return broad, boundary


def _load_pre2023_vital_flows(
    *,
    root: Path,
    demographic_raw: Path,
) -> dict[int, dict[str, dict[str, float]]]:
    mapping = load_region_mapping_manifest(root / MAPPING)
    regions = load_region_set_manifest(root / REGIONS).region_set
    source_to_region = mapping.source_to_target
    totals: dict[int, dict[str, dict[str, float]]] = {
        year: {
            region_id: {"population": 0.0, "births": 0.0, "deaths": 0.0}
            for region_id in regions.ids
        }
        for year in FIT_YEARS
    }

    with gzip.open(demographic_raw, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != WPP2024_FIELDS:
            raise ValueError("WPP demographic CSV schema does not match frozen contract")
        for row in reader:
            if not row["ISO3_code"]:
                continue
            year = int(row["Time"])
            if year not in FIT_YEARS:
                continue
            if row["Variant"] != WPP2024_VARIANT:
                raise ValueError("unexpected WPP demographic variant")
            parent_id = row["ParentID"]
            if parent_id not in source_to_region:
                raise ValueError(f"unmapped WPP parent group: {parent_id}")
            if not row["TPopulation1July"] or not row["CBR"] or not row["CDR"]:
                raise ValueError("missing WPP population/CBR/CDR fitting field")
            population_thousands = float(row["TPopulation1July"])
            cbr_per_thousand = float(row["CBR"])
            cdr_per_thousand = float(row["CDR"])
            if (
                population_thousands < 0
                or cbr_per_thousand < 0
                or cdr_per_thousand < 0
            ):
                raise ValueError("WPP fitting fields must be nonnegative")
            region = source_to_region[parent_id]
            totals[year][region]["population"] += population_thousands * 1000.0
            totals[year][region]["births"] += population_thousands * cbr_per_thousand
            totals[year][region]["deaths"] += population_thousands * cdr_per_thousand

    for year in FIT_YEARS:
        for region_id, values in totals[year].items():
            if values["population"] <= 0 or values["births"] <= 0 or values["deaths"] <= 0:
                raise ValueError(f"incomplete WPP vital-flow coverage: {year}/{region_id}")
    return totals


def derive_pre2023_rates(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    broad, boundary = _load_pre2023_cohort_state(root=root, age5_raw=age5_raw)
    vital = _load_pre2023_vital_flows(root=root, demographic_raw=demographic_raw)
    regions = load_region_set_manifest(root / REGIONS).region_set

    global_avg_stock = {
        cohort: sum(
            _mean(
                broad[2021][region_id][cohort],
                broad[2022][region_id][cohort],
            )
            for region_id in regions.ids
        )
        for cohort in AgeCohort
    }
    global_delta = {
        cohort: sum(
            broad[2022][region_id][cohort] - broad[2021][region_id][cohort]
            for region_id in regions.ids
        )
        for cohort in AgeCohort
    }
    global_age_outflow = {
        cohort: sum(
            _mean(
                boundary[2021][region_id][cohort],
                boundary[2022][region_id][cohort],
            )
            / 5.0
            for region_id in regions.ids
        )
        for cohort in BOUNDARY_GROUP
    }
    global_births = sum(
        _mean(vital[2021][region_id]["births"], vital[2022][region_id]["births"])
        for region_id in regions.ids
    )
    global_deaths = sum(
        _mean(vital[2021][region_id]["deaths"], vital[2022][region_id]["deaths"])
        for region_id in regions.ids
    )

    raw_global_mortality = {
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
    global_mortality = {
        cohort: _positive_rate(value, label=f"global mortality {cohort.value}")
        for cohort, value in raw_global_mortality.items()
    }

    global_total_stock = sum(global_avg_stock.values())
    observed_global_cdr = global_deaths / global_total_stock
    implied_global_cdr = (
        sum(global_mortality[c] * global_avg_stock[c] for c in AgeCohort)
        / global_total_stock
    )
    if observed_global_cdr <= 0 or implied_global_cdr <= 0:
        raise ValueError("global death-rate normalization must be positive")

    rates_by_region: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, Any] = {}
    for region_id in regions.ids:
        avg_stock = {
            cohort: _mean(
                broad[2021][region_id][cohort],
                broad[2022][region_id][cohort],
            )
            for cohort in AgeCohort
        }
        avg_births = _mean(
            vital[2021][region_id]["births"],
            vital[2022][region_id]["births"],
        )
        avg_deaths = _mean(
            vital[2021][region_id]["deaths"],
            vital[2022][region_id]["deaths"],
        )
        total = sum(avg_stock.values())
        regional_cdr = avg_deaths / total
        mortality_scale = regional_cdr / observed_global_cdr

        ageing = {
            cohort: _positive_rate(
                (
                    _mean(
                        boundary[2021][region_id][cohort],
                        boundary[2022][region_id][cohort],
                    )
                    / 5.0
                )
                / avg_stock[cohort],
                label=f"ageing {region_id}/{cohort.value}",
            )
            for cohort in BOUNDARY_GROUP
        }
        ageing[AgeCohort.OLDER_ADULT] = 0.0
        mortality = {
            cohort: _positive_rate(
                global_mortality[cohort] * mortality_scale,
                label=f"mortality {region_id}/{cohort.value}",
            )
            for cohort in AgeCohort
        }
        birth_rate = _positive_rate(
            avg_births / avg_stock[AgeCohort.YOUNG_ADULT],
            label=f"birth rate {region_id}",
        )

        rates_by_region[region_id] = {
            "birth_rate_per_young_adult": birth_rate,
            "mortality": {cohort.value: mortality[cohort] for cohort in AgeCohort},
            "ageing": {cohort.value: ageing[cohort] for cohort in AgeCohort},
        }
        diagnostics[region_id] = {
            "average_births_persons_per_year": avg_births,
            "average_deaths_persons_per_year": avg_deaths,
            "average_population_persons": total,
            "observed_crude_death_fraction_per_year": regional_cdr,
            "mortality_scale_vs_global": mortality_scale,
            "rates": rates_by_region[region_id],
        }

    receipt = {
        "schema_id": "WZ_DEMOGRAPHY_PRE2023_DYNAMICS_DERIVATION_RECEIPT_V1",
        "candidate_lineage_id": "WZ_DEMOGRAPHY_PRE2023_DYNAMICS_CANDIDATE_V1",
        "parameter_set_id": PARAMETER_SET_ID,
        "fit_years": list(FIT_YEARS),
        "max_fit_evidence_year": max(FIT_YEARS),
        "method": (
            "Regional births and ageing are derived from 2021-2022 WPP official "
            "estimate structure. The global age-specific mortality shape is the "
            "nonnegative residual of the 2021->2022 cohort continuity equations, "
            "then scaled to each macroregion's observed crude death level."
        ),
        "global": {
            "average_births_persons_per_year": global_births,
            "average_deaths_persons_per_year": global_deaths,
            "observed_crude_death_fraction_per_year": observed_global_cdr,
            "continuity_implied_crude_death_fraction_per_year": implied_global_cdr,
            "mortality": {
                cohort.value: global_mortality[cohort] for cohort in AgeCohort
            },
        },
        "regions": diagnostics,
        "holdout_used_for_fit": False,
    }
    return rates_by_region, receipt


def materialize_parameter_set(
    *,
    root: Path,
    rates_by_region: dict[str, dict[str, Any]],
    output_path: Path,
) -> str:
    payload = yaml.safe_load((root / BASE_PARAMETERS).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("base parameter set must be a mapping")
    default_region = payload["default_region"]
    if not isinstance(default_region, dict):
        raise TypeError("base default-region parameter block must be a mapping")

    payload["parameter_set_id"] = PARAMETER_SET_ID
    payload["region_overrides"] = {}
    for region_id, rates in rates_by_region.items():
        block = copy.deepcopy(default_region)
        block["demography"] = rates
        payload["region_overrides"][region_id] = block
    payload["migration_links"] = []
    payload["notes"] = (
        "Deterministically derived pre-2023 demographic dynamics candidate. "
        "All fitted evidence is dated 2021-2022; the 2023 holdout is excluded "
        "from parameter derivation. Rates remain provisional benchmark-comparison "
        "parameters and are not structurally identified calibration claims."
    )

    parameter_bytes = yaml.safe_dump(payload, sort_keys=False).encode("utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(parameter_bytes)
    return hashlib.sha256(parameter_bytes).hexdigest()


def execute_fit_score_compare(
    *,
    root: Path,
    age5_raw: Path,
    demographic_raw: Path,
    output_dir: Path,
    expected_source_commit: str | None = None,
) -> tuple[
    RuntimeReceipt,
    TemporalPopulationScoreReport,
    TemporalPopulationComparisonReport,
]:
    comparison_contract = load_temporal_population_comparison_contract(
        root / COMPARISON_CONTRACT
    )
    if max(FIT_YEARS) > comparison_contract.max_fit_evidence_year:
        raise ValueError("fit evidence exceeds frozen comparison-contract cutoff")
    if comparison_contract.candidate_parameter_set_id != PARAMETER_SET_ID:
        raise ValueError("candidate parameter-set identity does not match frozen contract")

    age_manifest = load_dataset_manifest(root / AGE5_MANIFEST)
    demographic_manifest = load_dataset_manifest(root / DEMOGRAPHIC_MANIFEST)
    if _sha256(age5_raw) != age_manifest.content_sha256:
        raise ValueError("age5 raw bytes do not match admitted manifest")
    if _sha256(demographic_raw) != demographic_manifest.content_sha256:
        raise ValueError("demographic raw bytes do not match admitted manifest")

    output_dir.mkdir(parents=True, exist_ok=True)
    parameter_path = output_dir / "derived-parameters.yaml"
    derivation_path = output_dir / "derivation-receipt.json"
    result_path = output_dir / "result.json"
    runtime_receipt_path = output_dir / "runtime-receipt.json"
    score_path = output_dir / "score-report.json"
    comparison_path = output_dir / "comparison-report.json"

    rates_by_region, derivation = derive_pre2023_rates(
        root=root,
        age5_raw=age5_raw,
        demographic_raw=demographic_raw,
    )
    parameter_sha256 = materialize_parameter_set(
        root=root,
        rates_by_region=rates_by_region,
        output_path=parameter_path,
    )
    derivation["source_inputs"] = {
        age_manifest.dataset_id: {
            "sha256": age_manifest.content_sha256,
            "length_bytes": age_manifest.content_length_bytes,
        },
        demographic_manifest.dataset_id: {
            "sha256": demographic_manifest.content_sha256,
            "length_bytes": demographic_manifest.content_length_bytes,
        },
    }
    derivation["parameter_set_sha256"] = parameter_sha256
    derivation_path.write_bytes(_canonical_json_bytes(derivation))

    runtime_receipt = execute_baseline_to_files(
        root=root,
        scenario_path=SCENARIO,
        data_bundle_path=DATA_BUNDLE,
        parameter_set_path=parameter_path,
        output_path=result_path,
        receipt_path=runtime_receipt_path,
        source_root=root,
        expected_source_commit=expected_source_commit,
    )
    if runtime_receipt.parameter_set.sha256 != parameter_sha256:
        raise ValueError("runtime receipt parameter digest does not match derived parameters")

    candidate_score = score_temporal_population_result(
        root=root,
        contract_path=root / SCORE_CONTRACT,
        result_path=result_path,
        receipt_path=runtime_receipt_path,
    )
    score_path.write_bytes(canonical_score_report_bytes(candidate_score))

    benchmark = TemporalPopulationScoreReport.model_validate_json(
        (root / comparison_contract.benchmark_score_path).read_bytes()
    )
    comparison = compare_temporal_population_scores(
        contract=comparison_contract,
        benchmark=benchmark,
        candidate=candidate_score,
    )
    comparison_path.write_bytes(canonical_comparison_report_bytes(comparison))
    return runtime_receipt, candidate_score, comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--age5-raw", type=Path, required=True)
    parser.add_argument("--demographic-raw", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/WORLD_ZERO_2022_TO_2023_PRE2023_DYNAMICS_V1"),
    )
    parser.add_argument("--expected-source-commit")
    args = parser.parse_args()

    receipt, score, comparison = execute_fit_score_compare(
        root=args.root.resolve(),
        age5_raw=args.age5_raw.resolve(),
        demographic_raw=args.demographic_raw.resolve(),
        output_dir=args.output_dir.resolve(),
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_PRE2023_RUNTIME_RECEIPT=" + receipt.model_dump_json())
    print("WZ_PRE2023_SCORE_REPORT=" + score.model_dump_json())
    print("WZ_PRE2023_COMPARISON=" + comparison.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
