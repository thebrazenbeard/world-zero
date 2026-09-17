from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from tools.verify_wheelhouse import verify_wheelhouse

TARGETS = {
    "cp312-win_amd64": {
        "python_version": "3.12",
        "implementation": "cp",
        "abi": "cp312",
        "platform": "win_amd64",
        "architecture": "x86_64",
    },
    "cp312-manylinux_x86_64": {
        "python_version": "3.12",
        "implementation": "cp",
        "abi": "cp312",
        "platform": "manylinux_2_17_x86_64",
        "architecture": "x86_64",
    },
    "cp313-win_amd64": {
        "python_version": "3.13",
        "implementation": "cp",
        "abi": "cp313",
        "platform": "win_amd64",
        "architecture": "x86_64",
    },
    "cp313-manylinux_x86_64": {
        "python_version": "3.13",
        "implementation": "cp",
        "abi": "cp313",
        "platform": "manylinux_2_17_x86_64",
        "architecture": "x86_64",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_download_command(
    requirements: Path,
    wheelhouse: Path,
    target: str,
    python_executable: str = sys.executable,
) -> list[str]:
    try:
        target_spec = TARGETS[target]
    except KeyError as exc:
        raise ValueError(f"unsupported wheelhouse target: {target}") from exc
    return [
        python_executable,
        "-m",
        "pip",
        "download",
        "--only-binary=:all:",
        "--dest",
        str(wheelhouse),
        "--requirement",
        str(requirements),
        "--platform",
        target_spec["platform"],
        "--python-version",
        target_spec["python_version"],
        "--implementation",
        target_spec["implementation"],
        "--abi",
        target_spec["abi"],
    ]


def build_wheelhouse(
    requirements: Path,
    wheelhouse: Path,
    target: str,
    python_executable: str = sys.executable,
) -> Path:
    if not requirements.is_file():
        raise ValueError(f"requirements file does not exist: {requirements}")
    if wheelhouse.exists() and any(wheelhouse.iterdir()):
        raise ValueError(f"wheelhouse must be empty before generation: {wheelhouse}")
    wheelhouse.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        build_download_command(requirements, wheelhouse, target, python_executable),
        check=True,
    )

    wheel_files = sorted(wheelhouse.glob("*.whl"))
    if not wheel_files:
        raise RuntimeError("pip produced no wheel artifacts")
    unexpected = [
        path.name
        for path in wheelhouse.iterdir()
        if path.is_file() and path.suffix != ".whl"
    ]
    if unexpected:
        raise RuntimeError(f"non-wheel artifacts produced: {unexpected}")

    copied_lock = wheelhouse / "requirements.lock"
    shutil.copyfile(requirements, copied_lock)
    spec = TARGETS[target]
    manifest = {
        "schema_version": "OFFLINE_WHEELHOUSE_MANIFEST_V1",
        "bundle_id": f"world-zero-bootstrap-{target}",
        "target": {
            "python_abi": spec["abi"],
            "platform": spec["platform"],
            "architecture": spec["architecture"],
        },
        "source_lock_sha256": _sha256(requirements),
        "allow_undeclared_wheels": False,
        "artifacts": [
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "package": None,
                "version": None,
            }
            for path in wheel_files
        ],
        "status": "CANDIDATE",
        "verification_receipt_ids": [],
    }
    (wheelhouse / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = verify_wheelhouse(wheelhouse)
    if not result.ok:
        raise RuntimeError(
            f"generated wheelhouse failed verification: {result.code} {result.details}"
        )
    return wheelhouse


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a World Zero offline wheelhouse")
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--target", choices=sorted(TARGETS), required=True)
    args = parser.parse_args()
    build_wheelhouse(args.requirements, args.wheelhouse, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
