"""Execute and score the frozen 2022 -> 2023 temporal population subject."""

from __future__ import annotations

import argparse
from pathlib import Path

from worldzero.models.execution import RuntimeReceipt, execute_baseline_to_files
from worldzero.validation.temporal_population import (
    TemporalPopulationScoreReport,
    canonical_score_report_bytes,
    score_temporal_population_result,
)

SCENARIO = Path("scenarios/2022_to_2023_temporal_score_v1.yaml")
DATA_BUNDLE = Path("data/bundles/WORLD_ZERO_2022_TEMPORAL_VALIDATION_DATA_V1.yaml")
PARAMETERS = Path(
    "scenarios/parameters/WORLD_ZERO_2022_TEMPORAL_SCORE_PROVISIONAL_V1.yaml"
)
SCORING_CONTRACT = Path(
    "science/scoring/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_CONTRACT_V1.yaml"
)


def execute_and_score(
    *,
    root: Path,
    output_dir: Path,
    expected_source_commit: str | None = None,
) -> tuple[RuntimeReceipt, TemporalPopulationScoreReport]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    receipt_path = output_dir / "runtime-receipt.json"
    score_path = output_dir / "score-report.json"

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
    report = score_temporal_population_result(
        root=root,
        contract_path=SCORING_CONTRACT,
        result_path=result_path,
        receipt_path=receipt_path,
    )
    score_path.write_bytes(canonical_score_report_bytes(report))
    return receipt, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/WORLD_ZERO_2022_TO_2023_TEMPORAL_SCORE_V1"),
    )
    parser.add_argument("--expected-source-commit")
    args = parser.parse_args()

    receipt, report = execute_and_score(
        root=args.root.resolve(),
        output_dir=args.output_dir,
        expected_source_commit=args.expected_source_commit,
    )
    print("WZ_TEMPORAL_RUNTIME_RECEIPT=" + receipt.model_dump_json())
    print("WZ_TEMPORAL_SCORE_REPORT=" + report.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
