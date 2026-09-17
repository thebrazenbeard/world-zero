from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "OFFLINE_WHEELHOUSE_MANIFEST_V1"


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    code: str
    details: tuple[str, ...] = ()


def load_manifest(wheelhouse: Path) -> dict[str, Any]:
    manifest_path = wheelhouse / "MANIFEST.json"
    if not manifest_path.is_file():
        raise ValueError("MANIFEST.json is missing")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid MANIFEST.json: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("MANIFEST.json root must be an object")  # noqa: TRY004
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(value.get("bundle_id"), str) or not value["bundle_id"]:
        raise ValueError("bundle_id must be a non-empty string")
    target = value.get("target")
    if not isinstance(target, dict):
        raise ValueError("target must be an object")  # noqa: TRY004
    for key in ("python_abi", "platform", "architecture"):
        if not isinstance(target.get(key), str) or not target[key]:
            raise ValueError(f"target.{key} must be a non-empty string")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("artifacts must be a list")  # noqa: TRY004
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_wheelhouse(wheelhouse: Path | str) -> VerificationResult:
    root = Path(wheelhouse)
    try:
        manifest = load_manifest(root)
    except ValueError as exc:
        return VerificationResult(False, "OFFLINE_BUNDLE_INVALID_MANIFEST", (str(exc),))

    declared: dict[str, dict[str, Any]] = {}
    for artifact in manifest["artifacts"]:
        if not isinstance(artifact, dict):
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                ("artifact must be an object",),
            )
        filename = artifact.get("filename")
        if not isinstance(filename, str) or not filename.endswith(".whl"):
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                ("artifact filename must end in .whl",),
            )
        if Path(filename).name != filename:
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                (f"unsafe artifact filename: {filename}",),
            )
        if filename in declared:
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                (f"duplicate artifact: {filename}",),
            )
        if not isinstance(artifact.get("size_bytes"), int) or artifact["size_bytes"] < 0:
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                (f"invalid size for {filename}",),
            )
        sha = artifact.get("sha256")
        if (
            not isinstance(sha, str)
            or len(sha) != 64
            or any(c not in "0123456789abcdef" for c in sha)
        ):
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_INVALID_MANIFEST",
                (f"invalid sha256 for {filename}",),
            )
        declared[filename] = artifact

    problems: list[str] = []
    for filename, artifact in declared.items():
        path = root / filename
        if not path.is_file():
            problems.append(f"missing:{filename}")
            continue
        if path.stat().st_size != artifact["size_bytes"]:
            problems.append(f"size:{filename}")
            continue
        if _sha256(path) != artifact["sha256"]:
            problems.append(f"sha256:{filename}")

    if problems:
        if any(item.startswith("missing:") for item in problems):
            return VerificationResult(False, "OFFLINE_BUNDLE_INCOMPLETE", tuple(problems))
        return VerificationResult(
            False,
            "OFFLINE_BUNDLE_TAMPERED_OR_DRIFTED",
            tuple(problems),
        )

    if not manifest.get("allow_undeclared_wheels", False):
        actual = {path.name for path in root.glob("*.whl") if path.is_file()}
        extras = sorted(actual - set(declared))
        if extras:
            return VerificationResult(
                False,
                "OFFLINE_BUNDLE_UNDECLARED_ARTIFACT",
                tuple(extras),
            )

    return VerificationResult(True, "PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a World Zero offline wheelhouse")
    parser.add_argument("wheelhouse", type=Path)
    args = parser.parse_args()
    result = verify_wheelhouse(args.wheelhouse)
    print(
        json.dumps(
            {"ok": result.ok, "code": result.code, "details": result.details},
            sort_keys=True,
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
