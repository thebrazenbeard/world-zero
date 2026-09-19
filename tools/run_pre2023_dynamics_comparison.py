"""Execute, score, and compare the frozen pre-2023 structural-ageing candidate."""

from __future__ import annotations

import argparse
from pathlib import Path

from worldzero.models.execution import RuntimeReceipt, execute_baseline_to_files
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
PARAMETERS = Path("scenarios/parameters/WORLD_ZERO_2022_PRE2023_DYNAMICS_V1.yaml")
SCORING_CONTRACT = Path(
    "science/scoring/"
    "WZ_DEMOGRAPHY_2022_TO_2023_PRE2023_DYNAMICS_SCORE_CONTRACT_V1.yaml"
)
COMPARISON_CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_SUCCESSOR_VS_PERSISTENCE_COMPARISON_V1.yaml"
)
BENCHMARK_SCORE = Path(
    "state/results/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_V1.json"
)


def execute_score_and_compare(
    *,
    root: Path,
    output_dir: Path,
    expected_source_commit: str | None = None,
) -> tuple[
    RuntimeReceipt,
    TemporalPopulationScoreReport,
    TemporalPopulationComparisonReport,
]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    receipt_path = output_dir / "runtime-receipt.json"
    score_path = output_dir / "score-report.json"
    comparison_path = output_dir / "comparison-report.json"

    receipt = execute_baseline_to_files(
        root=root,
        scenario_path=SCENARIO,
        data_bundle_path=DATA_BUNDLE,
        parameter_set_path=PARAMETERS,
        output_path=result_path,
        receipt_path=receipt_path,
        source_root=root,
        expected_source_commit=expected_source_commit,
    )
    score = score_temporal_population_result(
        root=root,
        contract_path=SCORING_CONTRACT,
        result_path=result_path,
        receipt_path=receipt_path,
    )
    score_path.write_bytes(canonical_score_report_bytes(score))

    contract = load_temporal_population_comparison_contract(
        root / COMPARISON_CONTRACT
    )
    benchmark = TemporalPopulationScoreReport.model_validate_json(
        (root / BENCHMARK_SCORE).read_bytes()
    )
    comparison = compare_temporal_population_scores(
        contract=contract,
        benchmark=benchmark,
        candidate=score,
    )
    comparison_path.write_bytes(canonical_comparison_report_bytes(comparison))
    return receipt, score, comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/WORLD_ZERO_2022_TO_2023_PRE2023_DYNAMICS_V1"),
    )
    parser.add_argument("--expected-source-commit")
    args = parser.parse_args()

    receipt, score, comparison = execute_score_and_compare(
        root=args.root.resolve(),
        output_dir=args.output_dir,
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_CANDIDATE_RUNTIME_RECEIPT=" + receipt.model_dump_json())
    print("WZ_CANDIDATE_SCORE_REPORT=" + score.model_dump_json())
    print("WZ_CANDIDATE_COMPARISON_REPORT=" + comparison.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
