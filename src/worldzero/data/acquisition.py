"""Fail-closed retrieval of externally hosted bytes bound by an admitted manifest."""

from __future__ import annotations

import hashlib
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .manifests import DatasetAdmissionStatus, load_dataset_manifest

_CHUNK_BYTES = 1024 * 1024


def _validate_https_url(url: str, *, label: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label} must be an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{label} must not contain URL credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{label} must not contain query parameters or fragments")


class _HTTPSOnlyRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_https_url(newurl, label="candidate redirect target")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_candidate(request: Request, *, timeout_seconds: float):
    opener = build_opener(_HTTPSOnlyRedirectHandler())
    return opener.open(request, timeout=timeout_seconds)


@dataclass(frozen=True, slots=True)
class VerifiedFetchResult:
    dataset_id: str
    requested_url: str
    resolved_url: str
    output_path: Path
    content_sha256: str
    content_length_bytes: int


def _copy_verified_candidate(
    stream: BinaryIO,
    *,
    output_path: Path,
    dataset_id: str,
    requested_url: str,
    resolved_url: str | None = None,
    expected_length: int,
    expected_sha256: str,
    replace_existing: bool = False,
) -> VerifiedFetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    written = 0
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".candidate",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            while True:
                chunk = stream.read(_CHUNK_BYTES)
                if not chunk:
                    break
                written += len(chunk)
                if written > expected_length:
                    raise ValueError("candidate payload exceeds admitted content length")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())

        if written != expected_length:
            raise ValueError("candidate payload length does not match admitted manifest")
        actual_sha256 = digest.hexdigest()
        if actual_sha256 != expected_sha256:
            raise ValueError("candidate payload digest does not match admitted manifest")

        if replace_existing:
            os.replace(temporary_path, output_path)
            temporary_path = None
        else:
            try:
                os.link(temporary_path, output_path)
            except FileExistsError as exc:
                raise ValueError(
                    "output path appeared during retrieval; refusing implicit replacement"
                ) from exc
            temporary_path.unlink()
            temporary_path = None
        return VerifiedFetchResult(
            dataset_id=dataset_id,
            requested_url=requested_url,
            resolved_url=requested_url if resolved_url is None else resolved_url,
            output_path=output_path,
            content_sha256=actual_sha256,
            content_length_bytes=written,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _paths_alias(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    if not left.exists() or not right.exists():
        return False
    try:
        return left.samefile(right)
    except OSError as exc:
        raise ValueError("dataset acquisition path identity could not be established") from exc


def fetch_admitted_dataset(
    manifest_path: Path,
    output_path: Path,
    *,
    candidate_url: str | None = None,
    timeout_seconds: float = 120.0,
    replace_existing: bool = False,
) -> VerifiedFetchResult:
    """Retrieve candidate bytes and publish them only after exact manifest verification."""

    if _paths_alias(manifest_path, output_path):
        raise ValueError("output path must not overwrite the governed source manifest")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    if output_path.exists() and not replace_existing:
        raise ValueError("output path already exists; explicit replace_existing=True is required")

    manifest = load_dataset_manifest(manifest_path)
    if manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
        raise ValueError("source manifest must be ADMITTED before governed retrieval")
    if manifest.content_length_bytes is None:
        raise ValueError("admitted source manifest must bind content length")

    source_url = manifest.source_url if candidate_url is None else candidate_url
    _validate_https_url(source_url, label="candidate URL")

    request = Request(
        source_url,
        headers={
            "Accept-Encoding": "identity",
            "User-Agent": "world-zero/0.1 admitted-source-fetch",
        },
    )
    with _open_candidate(request, timeout_seconds=timeout_seconds) as response:
        if response.status != 200:
            raise ValueError(f"candidate source returned HTTP {response.status}")
        resolved_url = response.geturl()
        _validate_https_url(resolved_url, label="candidate redirect target")

        declared_length = response.headers.get("Content-Length")
        if (
            declared_length is not None
            and int(declared_length) != manifest.content_length_bytes
        ):
            raise ValueError("candidate HTTP content length does not match admitted manifest")
        return _copy_verified_candidate(
            response,
            output_path=output_path,
            dataset_id=manifest.dataset_id,
            requested_url=source_url,
            resolved_url=resolved_url,
            expected_length=manifest.content_length_bytes,
            expected_sha256=manifest.content_sha256,
            replace_existing=replace_existing,
        )
