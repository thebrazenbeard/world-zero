"""Run the canonical World Zero V0 baseline and emit exact runtime receipts."""

from __future__ import annotations

import argparse
from pathlib import Path

from worldzero.models.execution import execute_baseline_to_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-root", type=Path, default=Path("."))
    parser.add_argument(
        "--scenario",
        type=Path,
        default=Path("scenarios/2026_baseline.yaml"),
    )
    parser.add_argument(
        "--data-bundle",
        type=Path,
        default=Path("data/bundles/WORLD_ZERO_2026_BASELINE_DATA_V0.yaml"),
    )
    parser.add_argument(
        "--parameter-set",
        type=Path,
        default=Path(
            "scenarios/parameters/WORLD_ZERO_2026_PROVISIONAL_EXECUTION_V1.yaml"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/WORLD_ZERO_2026_BASELINE/result.json"),
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("runs/WORLD_ZERO_2026_BASELINE/receipt.json"),
    )
    parser.add_argument("--expected-source-commit")
    parser.add_argument("--expected-source-tree")
    args = parser.parse_args()

    receipt = execute_baseline_to_files(
        root=args.root,
        scenario_path=args.scenario,
        data_bundle_path=args.data_bundle,
        parameter_set_path=args.parameter_set,
        output_path=args.output,
        receipt_path=args.receipt,
        source_root=args.source_root,
        expected_source_commit=args.expected_source_commit,
        expected_source_tree=args.expected_source_tree,
    )
    print(receipt.model_dump_json())


if __name__ == "__main__":
    main()
