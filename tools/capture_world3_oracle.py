from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import inspect
import json
import math
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from worldzero.reference.world3 import World3OracleExecutionSpec, World3ReferenceProfile


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def exact_commit_from_ref(implementation_ref: str) -> str:
    _, separator, commit = implementation_ref.rpartition("@")
    if not separator or len(commit) != 40:
        raise ValueError("implementation_ref does not contain an exact commit")
    return commit


def checkout_commit(checkout: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def format_number(value: Any) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("oracle output contains a non-finite value")
    return format(number, ".17g")


def serialize_fixture_csv(
    years: Sequence[Any],
    series: Mapping[str, Sequence[Any]],
    observable_order: Sequence[str],
) -> bytes:
    length = len(years)
    if any(len(series[observable]) != length for observable in observable_order):
        raise ValueError("oracle series lengths do not match the time grid")

    rows: list[list[str]] = [["YEAR", *observable_order]]
    for index, year in enumerate(years):
        rows.append(
            [
                format_number(year),
                *(
                    format_number(series[observable][index])
                    for observable in observable_order
                ),
            ]
        )

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def signature_defaults(callable_object: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for name, parameter in inspect.signature(callable_object).parameters.items():
        if name == "self" or parameter.default is inspect.Parameter.empty:
            continue
        value = parameter.default
        if value is None or isinstance(value, (bool, int, float, str)):
            defaults[name] = value
        else:
            defaults[name] = repr(value)
    return defaults


def package_version(module_name: str) -> str:
    module = importlib.import_module(module_name)
    version = getattr(module, "__version__", None)
    return str(version) if version is not None else "UNKNOWN"


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def capture(
    *,
    spec_path: Path,
    profile_path: Path,
    oracle_checkout: Path,
    output_dir: Path,
    capture_status: str,
) -> tuple[Path, Path]:
    spec = World3OracleExecutionSpec.model_validate(_load_yaml(spec_path))
    profile = World3ReferenceProfile.model_validate(_load_yaml(profile_path))
    if spec.profile_id != profile.profile_id:
        raise ValueError("oracle spec and reference profile ids do not match")

    expected_commit = exact_commit_from_ref(spec.implementation_ref)
    observed_commit = checkout_commit(oracle_checkout)
    if observed_commit != expected_commit:
        raise ValueError(
            f"oracle checkout mismatch: expected {expected_commit}, "
            f"observed {observed_commit}"
        )

    sys.path.insert(0, str(oracle_checkout))
    try:
        pyworld3 = importlib.import_module("pyworld3")
        world3_module = importlib.import_module("pyworld3.world3")
        world3_class = getattr(world3_module, "World3")
        model = world3_class(
            year_min=spec.start_year,
            year_max=spec.end_year,
            dt=spec.timestep_years,
        )

        for method_name in spec.initialization_sequence:
            method = getattr(model, method_name)
            if method_name == "set_world3_delay_functions":
                delay_method = "euler" if spec.delay_method == "EULER" else None
                if delay_method is None:
                    method()
                else:
                    method(method=delay_method)
            elif method_name == "run_world3":
                method(fast=spec.run_mode != "CHECKED_RESCHEDULE")
            else:
                method()

        years = list(model.time)
        if len(years) != spec.sample_count:
            raise ValueError(
                f"oracle produced {len(years)} samples; expected {spec.sample_count}"
            )
        if format_number(years[0]) != format_number(spec.start_year):
            raise ValueError("oracle time grid starts at the wrong year")
        if spec.endpoint_inclusive and format_number(years[-1]) != format_number(
            spec.end_year
        ):
            raise ValueError(
                "oracle time grid does not include the declared endpoint"
            )

        binding_map = {
            binding.observable_id: binding.implementation_name
            for binding in spec.observable_bindings
        }
        observable_order = [
            binding.observable_id for binding in spec.observable_bindings
        ]
        series = {
            observable: list(getattr(model, implementation_name))
            for observable, implementation_name in binding_map.items()
        }
        fixture_bytes = serialize_fixture_csv(years, series, observable_order)

        output_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = output_dir / "WORLD3_1974_PYWORLD3_STANDARD.csv"
        fixture_path.write_bytes(fixture_bytes)

        table_path = oracle_checkout / "pyworld3" / "functions_table_world3.json"
        metadata = {
            "capture_status": capture_status,
            "profile_id": profile.profile_id,
            "profile_file_sha256": sha256_file(profile_path),
            "oracle_id": spec.oracle_id,
            "oracle_spec_file_sha256": sha256_file(spec_path),
            "implementation_ref": spec.implementation_ref,
            "observed_checkout_commit": observed_commit,
            "python_version": platform.python_version(),
            "package_versions": {
                "pyworld3": str(getattr(pyworld3, "__version__", "UNKNOWN")),
                "numpy": package_version("numpy"),
                "scipy": package_version("scipy"),
                "matplotlib": package_version("matplotlib"),
            },
            "world3_init_defaults": signature_defaults(world3_class.__init__),
            "world3_constant_defaults": signature_defaults(
                world3_class.init_world3_constants
            ),
            "delay_defaults": signature_defaults(
                world3_class.set_world3_delay_functions
            ),
            "run_defaults": signature_defaults(world3_class.run_world3),
            "table_file_sha256": sha256_file(table_path),
            "sample_count": len(years),
            "fixture_sha256": sha256_bytes(fixture_bytes),
        }
        metadata_path = (
            output_dir / "WORLD3_1974_PYWORLD3_STANDARD.metadata.json"
        )
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return fixture_path, metadata_path
    finally:
        sys.path.remove(str(oracle_checkout))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--oracle-checkout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--capture-status",
        default="PROVISIONAL_ENV_DISCOVERY",
        choices=("PROVISIONAL_ENV_DISCOVERY", "FROZEN_ORACLE_CAPTURE"),
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    fixture_path, metadata_path = capture(
        spec_path=args.spec,
        profile_path=args.profile,
        oracle_checkout=args.oracle_checkout,
        output_dir=args.output_dir,
        capture_status=args.capture_status,
    )
    print(fixture_path)
    print(metadata_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
